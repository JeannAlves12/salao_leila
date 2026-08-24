from django.urls import path
from appointments.views import client_views, owner_views, service_views, auth_views


urlpatterns = [
    # Rotas Públicas/Autenticação
    path('', service_views.service_list_view, name='service_list'),
    path('signup/', auth_views.signup_view, name='signup'),
    path('entrar/', auth_views.login_redirect_view, name='login_redirect_view'),

    # Rotas do Cliente
    path('agendar/', client_views.new_appointment_view, name='new_appointment'),
    path('history/', client_views.appointment_history_view, name='appointment_history'),
    path('editar/<int:appointment_id>/', client_views.edit_appointment_view, name='edit_appointment'),

    # rota inteligente, funciona para os dois
    path('cancelar/<int:appointment_id>/', client_views.cancel_appointment_view, name='cancel_appointment'),

    # Rotas da Gerência
    path('gerencia/', owner_views.owner_dashboard_view, name='owner_dashboard'),
    path('gerencia/servico/<int:service_id>/', service_views.service_detail_view, name='owner_service_detail'),
    path('gerencia/item/<int:item_id>/status/', owner_views.update_item_status_view, name='update_item_status'),
    path('gerencia/agendamento/<int:appointment_id>/confirmar/', owner_views.toggle_appointment_confirmation_view, name='toggle_appointment_confirmation'),
    path('gerencia/editar/<int:appointment_id>/', owner_views.owner_edit_appointment_view, name='owner_edit_appointment'),
    path('gerencia/agendar/', owner_views.owner_new_appointment_view, name='owner_new_appointment'),
]
