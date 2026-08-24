from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from .models import Service, Appointment, AppointmentItem
from .forms import AppointmentForm, OwnerAppointmentForm, ServiceForm
from .services import check_existing_appointment_this_week, can_edit_appointment, get_owner_dashboard_metrics


def service_list_view(request):
    services = Service.objects.all()
    return render(request, 'appointments/service_list.html', {'services': services})


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('service_list')
    else:
        form = UserCreationForm()
    return render(request, 'appointments/signup.html', {'form': form})


@login_required
def login_redirect_view(request):
    if request.user.is_staff:
        return redirect('owner_dashboard')
    return redirect('service_list')


@login_required
def new_appointment_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        
        ignore_suggestion = request.POST.get('ignore_suggestion', False)
        accept_suggestion = request.POST.get('accept_suggestion', False)
        suggested_date = request.POST.get('suggested_date', None)

        if form.is_valid():
            desired_date = form.cleaned_data['date_time']
            
            if accept_suggestion and suggested_date:
                desired_date = parse_datetime(suggested_date)

            if not ignore_suggestion and not accept_suggestion:
                existing_appointment = check_existing_appointment_this_week(request.user, desired_date)

                if existing_appointment:
                    return render(request, 'appointments/suggestion.html', {
                        'existing_date': existing_appointment.date_time,
                        'desired_date': desired_date,
                        'services_list': request.POST.getlist('services'),
                    })
            
            appointment, created = Appointment.objects.get_or_create(
                client=request.user,
                date_time=desired_date
            )

            if not created:
                appointment.is_confirmed = False
                appointment.save()
            
            selected_services = form.cleaned_data['services']
            for service in selected_services:
                AppointmentItem.objects.get_or_create(
                    appointment=appointment,
                    service=service,
                    defaults={'status': 'pendente'}
                )
            
            return redirect('appointment_history')
    else:
        service_id = request.GET.get('service_id')

        if service_id:
            form = AppointmentForm(initial={'services': [service_id]})
        else:
            form = AppointmentForm()

    return render(request, 'appointments/client_new_appointment.html', {'form': form})


@login_required
def appointment_history_view(request):
    appointments = Appointment.objects.filter(client=request.user).order_by('-date_time')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        appointments = appointments.filter(date_time__date__gte=start_date)
    if end_date:
        appointments = appointments.filter(date_time__date__lte=end_date)

    paginator = Paginator(appointments, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'appointments/client_history.html', {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date
    })


@login_required
def edit_appointment_view(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id, client=request.user)

    if not can_edit_appointment(appointment):
        messages.warning(request, 'Este agendamento ocorre em menos de 2 dias. Por favor, ligue para o salão para alterar.')
        return redirect('appointment_history')

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.is_confirmed = False
            appointment.save()
            appointment.items.all().delete()
            selected_services = form.cleaned_data['services']
            for service in selected_services:
                AppointmentItem.objects.create(
                    appointment=appointment,
                    service=service,
                    status='pendente'
                )
            messages.success(request, 'Agendamento atualizado com sucesso! Ele foi enviado novamente para a confirmação da gerência.')
            return redirect('appointment_history')
    else:
        initial_services = appointment.items.values_list('service', flat=True)
        formatted_date = appointment.date_time.strftime('%Y-%m-%dT%H:%M')
        
        form = AppointmentForm(instance=appointment, initial={
            'services': initial_services,
            'date_time': formatted_date
        })
    
    return render(request, 'appointments/client_edit_appointment.html', {'form': form, 'appointment': appointment})


@login_required
def cancel_appointment_view(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)

    if appointment.client != request.user and not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para cancelar este agendamento!')
        return redirect('service_list')
    
    if not request.user.is_staff and not can_edit_appointment(appointment):
        messages.error(request, 'Agendamento acontece em menos de 2 dias. Favor ligar para o estabelecimento para cancelar!')
        return redirect('appointment_history')
    
    appointment.delete()
    messages.success(request, 'Agendamento cancelado com sucesso!')

    if request.user.is_staff:
        return redirect('owner_dashboard')
    return redirect('appointment_history')


@staff_member_required
def owner_dashboard_view(request):
    filter_date = request.GET.get('week_filter')
    metrics = get_owner_dashboard_metrics(filter_date)
    return render(request, 'appointments/owner_dashboard.html', metrics)


@staff_member_required
def update_item_status_view(request, item_id):
    """ Permite o Dono alterar o status de cada sesrviço."""
    item = AppointmentItem.objects.get(id=item_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(AppointmentItem.STATUS_CHOICES):
            item.status = new_status
            item.save()
            messages.success(request, f"Status do serviço '{item.service.name}' atualizado com sucesso!")
    return redirect('owner_dashboard')


@staff_member_required
def toggle_appointment_confirmation_view(request, appointment_id):
    """Permite o dono confirmar o agendamento completo do cliente."""
    appt = Appointment.objects.get(id=appointment_id)
    appt.is_confirmed = not appt.is_confirmed
    appt.save()
    messages.success(request, f"Confirmação do agendamento de {appt.client.username} alterada.")
    return redirect('owner_dashboard')


@staff_member_required
def owner_edit_appointment_view(request, appointment_id):
    """Permite à dona alterar qualquer agendamento, burlando a regra dos 2 dias."""
    appointment = Appointment.objects.get(id=appointment_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save()
            
            appointment.items.all().delete()
            selected_services = form.cleaned_data['services']
            for service in selected_services:
                AppointmentItem.objects.create(
                    appointment=appointment,
                    service=service,
                    status='pendente'
                )
            messages.success(request, f"Agendamento de {appointment.client.username} alterado com sucesso!")
            return redirect('owner_dashboard')
    else:
        initial_services = appointment.items.values_list('service', flat=True)
        formatted_date = appointment.date_time.strftime('%Y-%m-%dT%H:%M')
        
        form = AppointmentForm(instance=appointment, initial={
            'services': initial_services,
            'date_time': formatted_date
        })
    return render(request, 'appointments/owner_edit_appointment.html', {'form': form, 'appointment': appointment})


@staff_member_required
def owner_new_appointment_view(request):
    """Permite a dona agendar um serviço para uma cliente existente."""
    if request.method == 'POST':
        form = OwnerAppointmentForm(request.POST)
        if form.is_valid():
            appointment = Appointment.objects.create(
                client=form.cleaned_data['client'],
                date_time=form.cleaned_data['date_time']
            )
            selected_services = form.cleaned_data['services']
            for service in selected_services:
                AppointmentItem.objects.create(
                    appointment=appointment,
                    service=service,
                    status='pendente'
                )
            messages.success(request, f"Atendimento agendado para {appointment.client.username} com sucesso!")
            return redirect('owner_dashboard')
    else:
        form = OwnerAppointmentForm()
    return render(request, 'appointments/owner_new_appointment.html', {'form': form})


@staff_member_required
def service_detail_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            messages.success(request, f"Serviço {service.name} alterado com sucesso.")
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'appointments/owner_service_detail.html', {'form': form, 'service': service})
