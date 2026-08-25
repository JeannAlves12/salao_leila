from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import (
    ListView, UpdateView, TemplateView, CreateView, View, RedirectView, DeleteView
)

# Importações absolutas do seu próprio app
from appointments.models import Service, Appointment, AppointmentItem
from appointments.forms import ServiceForm, OwnerAppointmentForm
from appointments.services import can_edit_appointment, get_owner_dashboard_metrics

# ==========================================
# EXEMPLO 1: Listando os Serviços
# Equivalente à sua service_list_view
# ==========================================
class ServiceListView(ListView):
    model = Service
    template_name = 'appointments/service_list.html'
    
    context_object_name = 'services'


# ==========================================
# EXEMPLO 2: Editando um Serviço
# Equivalente à sua service_detail_view
# ==========================================
class ServiceUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'appointments/owner_service_detail.html'

    pk_url_kwarg = 'service_id' 
    
    success_url = reverse_lazy('service_list') 
    
    success_message = "Serviço %(name)s alterado com sucesso."

    def test_func(self):
        return self.request.user.is_staff


# ==========================================
# EXEMPLO 3: Cadastro de Usuário (Signup)
# Equivalente à sua signup_view
# ==========================================
class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'appointments/signup.html'
    success_url = reverse_lazy('service_list')

    def form_valid(self, form):
        response = super().form_valid(form) 
        
        login(self.request, self.object)    
        
        return response

# ==========================================
# EXEMPLO 4: Redirecionamento Pós-Login
# Equivalente à sua login_redirect_view
# ==========================================
class LoginRedirectView(LoginRequiredMixin, RedirectView):
    
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_staff:
            return reverse_lazy('owner_dashboard')
        return reverse_lazy('service_list')


# ==========================================
# EXEMPLO 5: Histórico da Cliente com Filtros
# Equivalente à sua appointment_history_view
# ==========================================
class ClientHistoryView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/client_history.html'
    
    context_object_name = 'page_obj'
    
    paginate_by = 5 

    def get_queryset(self):
        qs = Appointment.objects.filter(client=self.request.user).order_by('-date_time')
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            qs = qs.filter(date_time__date__gte=start_date)
        if end_date:
            qs = qs.filter(date_time__date__lte=end_date)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['start_date'] = self.request.GET.get('start_date')
        context['end_date'] = self.request.GET.get('end_date')
        return context


# ==========================================
# EXEMPLO 6: Cancelamento com Trava de Segurança
# Equivalente à sua cancel_appointment_view
# ==========================================
class ClientCancelView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Appointment
    pk_url_kwarg = 'appointment_id'
    
    success_url = reverse_lazy('appointment_history')

    def test_func(self):
        appointment = self.get_object()
        
        if self.request.user.is_staff:
            return True
            
        if appointment.client != self.request.user:
            return False
            
        return can_edit_appointment(appointment)

    def handle_no_permission(self):
        messages.error(self.request, 'Você não tem permissão para cancelar ou o prazo de 2 dias expirou!')
        return redirect('appointment_history')
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Agendamento cancelado com sucesso!')
        return super().delete(request, *args, **kwargs)


# ==========================================
# SUPER PODER: Criando nosso próprio Mixin
# ==========================================
class StaffRequiredMixin(UserPassesTestMixin):
    """
    Substitui o @staff_member_required. 
    Podemos herdar essa classe em qualquer View que seja exclusiva da Dona.
    """
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, 'Acesso restrito à gerência.')
        return redirect('service_list')


# ==========================================
# EXEMPLO 7: Dashboard da Gerência
# Equivalente à sua owner_dashboard_view
# ==========================================
class OwnerDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'appointments/owner_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_date = self.request.GET.get('week_filter')
        
        metrics = get_owner_dashboard_metrics(filter_date)
        
        context.update(metrics)
        return context


# ==========================================
# EXEMPLO 8: Agendamento pela Gerência
# Equivalente à sua owner_new_appointment_view
# ==========================================
class OwnerCreateAppointmentView(StaffRequiredMixin, CreateView):
    form_class = OwnerAppointmentForm
    template_name = 'appointments/owner_new_appointment.html'
    success_url = reverse_lazy('owner_dashboard')

    def form_valid(self, form):
        appointment = form.save()
        
        selected_services = form.cleaned_data['services']
        for service in selected_services:
            AppointmentItem.objects.create(
                appointment=appointment,
                service=service,
                status='pendente'
            )
        
        messages.success(self.request, f"Atendimento agendado para {appointment.client.username} com sucesso!")
        
        return super().form_valid(form)


# ==========================================
# EXEMPLO 9: Ações Rápidas sem Tela (Toggle)
# Equivalente à sua toggle_appointment_confirmation_view
# ==========================================
class ToggleConfirmationView(StaffRequiredMixin, View):
    
    def get(self, request, appointment_id):
        appt = get_object_or_404(Appointment, id=appointment_id)
        appt.is_confirmed = not appt.is_confirmed
        appt.save()
        
        messages.success(request, f"Confirmação do agendamento de {appt.client.username} alterada.")
        return redirect('owner_dashboard')
