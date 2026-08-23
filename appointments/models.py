from django.db import models
from django.contrib.auth.models import User


class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name} - R${self.price}"


class Appointment(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    date_time = models.DateTimeField()
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment: {self.client.username} - {self.date_time.strftime('%d/%m/%Y %H:%M')}"


class AppointmentItem(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.RESTRICT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    def __str__(self):
        return f"{self.service.name} ({self.get_status_display()}"
