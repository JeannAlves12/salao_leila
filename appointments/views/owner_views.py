from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from appointments.models import Appointment, AppointmentItem
from appointments.forms import AppointmentForm, OwnerAppointmentForm
from appointments.services import get_owner_dashboard_metrics


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
