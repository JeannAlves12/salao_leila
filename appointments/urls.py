from django.urls import path
from . import views

urlpatterns = [
    # Rotas Públicas/Autenticação
    path('', views.service_list_view, name='service_list'),
    path('signup/', views.signup_view, name='signup'),
    path('entrar/', views.login_redirect_view, name='login_redirect_view'),
    
    # Rotas do Cliente
    path('agendar/', views.new_appointment_view, name='new_appointment'),
    path('history/', views.appointment_history_view, name='appointment_history'),
    path('editar/<int:appointment_id>/', views.edit_appointment_view, name='edit_appointment'),
    
    # Rotas da Gerência
    path('gerencia/', views.owner_dashboard_view, name='owner_dashboard'),
    path('gerencia/item/<int:item_id>/status/', views.update_item_status_view, name='update_item_status'),
    path('gerencia/agendamento/<int:appointment_id>/confirmar/', views.toggle_appointment_confirmation_view, name='toggle_appointment_confirmation'),
    path('gerencia/editar/<int:appointment_id>/', views.owner_edit_appointment_view, name='owner_edit_appointment'),
    path('gerencia/agendar/', views.owner_new_appointment_view, name='owner_new_appointment'),
]