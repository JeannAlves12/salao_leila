from django.urls import path

# 1. Importando as nossas novas Class-Based Views
from appointments.cbv_examples import (
    ServiceListView, ServiceUpdateView, SignUpView, LoginRedirectView,
    ClientHistoryView, ClientCancelView, OwnerDashboardView, 
    OwnerCreateAppointmentView, ToggleConfirmationView
)

# 2. Importando as funções clássicas para as rotas que não convertemos
from appointments.views import client_views, owner_views

urlpatterns = [
    # ==========================================
    # Rotas Públicas/Autenticação
    # ==========================================
    path('', ServiceListView.as_view(), name='service_list'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('entrar/', LoginRedirectView.as_view(), name='login_redirect_view'),
    
    # ==========================================
    # Rotas do Cliente
    # ==========================================
    # Mantida como Função (FBV) porque não a convertemos no cbv_examples
    path('agendar/', client_views.new_appointment_view, name='new_appointment'),
    
    path('history/', ClientHistoryView.as_view(), name='appointment_history'),
    
    # Mantida como Função (FBV)
    path('editar/<int:appointment_id>/', client_views.edit_appointment_view, name='edit_appointment'),
    
    # Rota inteligente (CBV)
    path('cancelar/<int:appointment_id>/', ClientCancelView.as_view(), name='cancel_appointment'),

    # ==========================================
    # Rotas da Gerência
    # ==========================================
    path('gerencia/', OwnerDashboardView.as_view(), name='owner_dashboard'),
    path('gerencia/servico/<int:service_id>/', ServiceUpdateView.as_view(), name='owner_service_detail'),
    
    # Mantidas como Funções (FBV)
    path('gerencia/item/<int:item_id>/status/', owner_views.update_item_status_view, name='update_item_status'),
    path('gerencia/editar/<int:appointment_id>/', owner_views.owner_edit_appointment_view, name='owner_edit_appointment'),
    
    path('gerencia/agendamento/<int:appointment_id>/confirmar/', ToggleConfirmationView.as_view(), name='toggle_appointment_confirmation'),
    path('gerencia/agendar/', OwnerCreateAppointmentView.as_view(), name='owner_new_appointment'),
]