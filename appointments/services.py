from .models import Appointment
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import timedelta


def check_existing_appointment_this_week(user, desired_date):
    """
    Regra de negocio: vai verificar se a cliente ja possui um agendamento na mesma e ano. 
    Retorna o objeto Appointment se existir, ou None caso contrario.
    """
    week = desired_date.isocalendar()[1]
    year = desired_date.year

    existing_appointment = Appointment.objects.filter(
        client=user,
        date_time__week=week,
        date_time__year=year
    ).first()

    return existing_appointment


def can_edit_appointment(appointment):
    """
    Verifica se o agendamento está a mais de 2 dias de distância da data atual.
    Retorna True se puder editar, False caso contrário.
    """
    now = timezone.now()
    time_difference = appointment.date_time - now

    if time_difference >= timedelta(days=2):
        return True
    return False


def get_owner_dashboard_metrics(base_date=None):
    """
    Calcula o faturamento semanal e retorna todos os agendamentos para o painel da Leila.
    """
    if base_date:
        now = parse_date(base_date)
        if not now:
            now = timezone.now().date()
    else:
        now = timezone.now().date()
    
    start_of_week = now - timedelta(days=now.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    appointments = Appointment.objects.filter(
        date_time__date__gte=start_of_week, 
        date_time__date__lte=end_of_week
    ).order_by('date_time')

    weekly_revenue = 0
    for appt in appointments:
        for item in appt.items.exclude(status='cancelado'):
            weekly_revenue += item.service.price
    
    return {
        'appointments': appointments,
        'weekly_revenue': weekly_revenue,
        'total_appointments': appointments.count(),
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'selected_date': now.strftime('%Y-%m-%d')
    }