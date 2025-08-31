from django.urls import path
from . import views

app_name = 'machine'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/info/', views.machine_info, name='machine_info'),
    path('api/status/', views.machine_status, name='machine_status'),
    path('api/connect/', views.connect_machine, name='connect_machine'),
    path('api/disconnect/', views.disconnect_machine, name='disconnect_machine'),
    path('api/deliver/', views.deliver_coffee, name='deliver_coffee'),
    path('api/stop/', views.stop_delivery, name='stop_delivery'),
    path('api/purge/', views.start_purge, name='start_purge'),
    path('api/health/', views.health_check, name='health_check'),
    path('api/history/', views.delivery_history, name='delivery_history'),
    path('api/logs/', views.maintenance_logs, name='maintenance_logs'),
    path('api/test/', views.test_post, name='test_post'),
]