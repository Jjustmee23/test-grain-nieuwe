
from django.urls import path
from .views import *
from .views_new import testmill
urlpatterns = [
    path('', index, name='index'),
    path('manage-admin/', manage_admin_view, name='manage_admin'),
    path('test/', testmill, name='mill'),
    path('view-statistics/<int:factory_id>/', view_statistics, name='view_statistics'),
    path('manage-devices/', manage_devices, name='manage_devices'),


    path('contact/', contact_views.contact, name='contact'),
    path('contact/success/', contact_views.contact_success, name='contact_success'),
    path('tickets/', contact_views.my_tickets, name='my_tickets'),
    path('tickets/<int:ticket_id>/update/', contact_views.ticket_update, name='ticket_update'),
    path('resolve-door-alert/<int:log_id>/', resolve_door_alert, name='resolve_door_alert'),

    
]
