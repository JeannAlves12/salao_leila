from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from appointments.models import Appointment, AppointmentItem
from appointments.forms import AppointmentForm
from appointments.services import check_existing_appointment_this_week, can_edit_appointment, auto_complete_past_appointments


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
    auto_complete_past_appointments(request.user)
    appointments = Appointment.objects.filter(client=request.user).order_by('date_time')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date or end_date:
        if start_date:
            appointments = appointments.filter(date_time__date__gte=start_date)
        if end_date:
            appointments = appointments.filter(date_time__date__lte=end_date)
    else:
        today = timezone.now().date()
        appointments = appointments.filter(date_time__date__gte=today)

    paginator = Paginator(appointments, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    agora = timezone.now()

    return render(request, 'appointments/client_history.html', {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'agora': agora
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
