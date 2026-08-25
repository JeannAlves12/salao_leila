from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from appointments.models import Appointment, Service
from appointments.services import can_edit_appointment, check_existing_appointment_this_week


class AppointmentRulesTestCase(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(username='cliente_teste', password='password123')
        self.service = Service.objects.create(name='Corte de Cabelo', price=50.00, duration=30)

    def test_can_edit_appointment_allowed(self):
        future_date = timezone.now() + timedelta(days=3)
        appointment = Appointment.objects.create(client=self.client_user, date_time=future_date)

        self.assertTrue(can_edit_appointment(appointment))

    def test_can_edit_appointment_blocked(self):
        near_date = timezone.now() + timedelta(hours=24)
        appointment = Appointment.objects.create(client=self.client_user, date_time=near_date)

        self.assertFalse(can_edit_appointment(appointment))

    def test_suggest_same_date_this_week(self):
        base_date = timezone.now() + timedelta(days=2)
        appointment = Appointment.objects.create(client=self.client_user, date_time=base_date)

        desired_date = base_date + timedelta(hours=2)

        existing_appt = check_existing_appointment_this_week(self.client_user, desired_date)

        self.assertIsNotNone(existing_appt)
        self.assertEqual(existing_appt.date_time, base_date)

    def test_no_suggestion_different_week(self):
        base_date = timezone.now()
        Appointment.objects.create(client=self.client_user, date_time=base_date)

        desired_date = base_date + timedelta(days=15)

        existing_appt = check_existing_appointment_this_week(self.client_user, desired_date)

        self.assertIsNone(existing_appt)
