from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, AppointmentItem, Service
from django.contrib.auth.models import User


class AppointmentForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Quais serviços você deseja agendar?"
    )

    class Meta:
        model = Appointment
        fields = ['date_time', 'services']
        widgets= {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        }
        labels = {
            'date_time': 'Data e Hora do Agendamento'
        }

    def clean(self):
        """
        Validações customizadas para a data e hora do agendamento usando o método mestre.
        """
        cleaned_data = super().clean()
        date_time = cleaned_data.get('date_time')
        services = cleaned_data.get('services')

        if date_time and services:
            local_dt = timezone.localtime(date_time)

            if local_dt < timezone.localtime(timezone.now()):
                self.add_error('date_time', "Não é possível agendar em datas ou horários que já passaram.")

            if local_dt.weekday() == 6:
                self.add_error('date_time', "O salão não funciona aos domingos. Escolha de Segunda a Sábado.")

            if local_dt.hour < 8 or local_dt.hour >= 18:
                self.add_error('date_time', "O horário de funcionamento é das 08:00 às 18:00.")

            total_duration = sum(service.duration for service in services)
            new_start = local_dt
            new_end = new_start + timedelta(minutes=total_duration)

            day_start = new_start.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            existing_appointments = Appointment.objects.filter(
                date_time__gte=day_start,
                date_time__lt=day_end
            )
            
            if self.instance and self.instance.pk:
                existing_appointments = existing_appointments.exclude(pk=self.instance.pk)
                
            for appt in existing_appointments:
                appt_start = timezone.localtime(appt.date_time)
                
                # Soma a duração de todos os serviços deste agendamento existente (ignorando cancelados)
                appt_duration = sum(
                    item.service.duration for item in appt.items.exclude(status='cancelado')
                )
                
                if appt_duration == 0:
                    continue
                    
                appt_end = appt_start + timedelta(minutes=appt_duration)

                # Regra Matemática de Interseção de Tempo
                if new_start < appt_end and new_end > appt_start:
                    self.add_error(
                        'date_time', 
                        f"Horário indisponível. Já existe um atendimento das {appt_start.strftime('%H:%M')} às {appt_end.strftime('%H:%M')}."
                    )
                    break

        return cleaned_data


class OwnerAppointmentForm(AppointmentForm):
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        label="Selecione um Cliente",
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )
    
    class Meta(AppointmentForm.Meta):
        fields = ['client', 'date_time', 'services']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'price', 'duration']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Corte de Cabelo'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Ex: 50.00'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Duração em minutos'
            }),
        }
        labels = {
            'name': 'Nome do Serviço',
            'price': 'Preço (R$)',
            'duration': 'Duração (minutos)'
        }
