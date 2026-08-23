from django import forms
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
        fields = ['date_time']
        widgets= {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        }
        labels = {
            'date_time': 'Data e Hora do Agendamento'
        }


class OwnerAppointmentForm(AppointmentForm):
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        label="Selecione um Cliente",
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )
    
    class Meta(AppointmentForm.Meta):
        fields = ['client', 'date_time', 'services']