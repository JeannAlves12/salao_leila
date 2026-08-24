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
    
    # O padrão do Django seria enviar os dados para o HTML com o nome 'object_list'.
    # Como no seu HTML você usou {% for service in services %}, nós avisamos isso ao Django aqui:
    context_object_name = 'services'


# ==========================================
# EXEMPLO 2: Editando um Serviço
# Equivalente à sua service_detail_view
# ==========================================
class ServiceUpdateView(UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'appointments/owner_service_detail.html'
    
    # Dizemos ao Django que na URL usamos <int:service_id> em vez do padrão <int:pk>
    pk_url_kwarg = 'service_id' 
    
    # Para onde redirecionar após o POST ser salvo com sucesso
    success_url = reverse_lazy('service_list') 
    
    # Mensagem de sucesso (o %(name)s puxa dinamicamente o nome do serviço salvo)
    success_message = "Serviço %(name)s alterado com sucesso."

    # Esta função substitui o decorador @staff_member_required
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

    # A CreateView salva o formulário, mas não faz o login automático.
    # Por isso, sobrescrevemos o método form_valid para adicionar o login.
    def form_valid(self, form):
        # super().form_valid(form) salva o novo usuário no banco de dados
        response = super().form_valid(form) 
        
        # self.object armazena a instância do usuário recém-criado
        login(self.request, self.object)    
        
        return response

# ==========================================
# EXEMPLO 4: Redirecionamento Pós-Login
# Equivalente à sua login_redirect_view
# ==========================================
class LoginRedirectView(LoginRequiredMixin, RedirectView):
    
    # A RedirectView redireciona para uma URL. Como a nossa URL 
    # depende de quem está logado, usamos o get_redirect_url.
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
    
    # A ListView injeta a paginação automaticamente no HTML se usarmos o nome 'page_obj'
    context_object_name = 'page_obj'
    
    # Lembra das linhas de Paginator() na sua função? Na CBV, basta UMA linha:
    paginate_by = 5 

    # Sobrescrevemos a busca no banco para trazer apenas os da cliente logada e aplicar filtros
    def get_queryset(self):
        qs = Appointment.objects.filter(client=self.request.user).order_by('-date_time')
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            qs = qs.filter(date_time__date__gte=start_date)
        if end_date:
            qs = qs.filter(date_time__date__lte=end_date)
            
        return qs

    # Injetamos as datas de volta no contexto do HTML para manter os filtros preenchidos na tela
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
    
    # Para onde ir depois de deletar com sucesso
    success_url = reverse_lazy('appointment_history')

    # A mágica da segurança: O UserPassesTestMixin roda esta função ANTES de tudo.
    # Se retornar False, a view é bloqueada imediatamente.
    def test_func(self):
        appointment = self.get_object() # Pega o agendamento do banco sozinho
        
        # Dona pode tudo
        if self.request.user.is_staff:
            return True
            
        # Cliente não pode cancelar agendamento dos outros
        if appointment.client != self.request.user:
            return False
            
        # Aplica a sua regra de negócio dos 2 dias (que criamos no models ou services)
        return can_edit_appointment(appointment)

    # O que acontece se a função acima retornar False? (Se o teste falhar)
    def handle_no_permission(self):
        messages.error(self.request, 'Você não tem permissão para cancelar ou o prazo de 2 dias expirou!')
        return redirect('appointment_history')
        
    # Método executado quando a deleção de fato ocorre
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

    # Como o Dashboard pega dados variados, usamos a TemplateView 
    # e sobrescrevemos o contexto para injetar as métricas nela.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_date = self.request.GET.get('week_filter')
        
        # Chama a sua regra de negócio isolada no services.py
        metrics = get_owner_dashboard_metrics(filter_date)
        
        # Mescla as métricas com o contexto do HTML
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

    # Interceptamos o momento que o form principal é validado para 
    # salvar os serviços dentro do AppointmentItem
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
        
        # Retorna o comportamento normal (redirecionar para a success_url)
        return super().form_valid(form)


# ==========================================
# EXEMPLO 9: Ações Rápidas sem Tela (Toggle)
# Equivalente à sua toggle_appointment_confirmation_view
# ==========================================
class ToggleConfirmationView(StaffRequiredMixin, View):
    # Usamos a View base genérica quando não queremos renderizar um HTML,
    # apenas processar um clique em um botão e redirecionar.
    
    def get(self, request, appointment_id):
        appt = get_object_or_404(Appointment, id=appointment_id)
        appt.is_confirmed = not appt.is_confirmed
        appt.save()
        
        messages.success(request, f"Confirmação do agendamento de {appt.client.username} alterada.")
        return redirect('owner_dashboard')
