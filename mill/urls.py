
from django.urls import path
from .views import index, manage_admin_view, contact_views
from .views_new import testmill
urlpatterns = [
    path('', index, name='index'),
    path('manage-admin/', manage_admin_view, name='manage_admin'),
    path('test/', testmill, name='mill'),
    path('contact/', contact_views.contact, name='contact'),
    path('contact/success/', contact_views.contact_success, name='contact_success'),
    path('tickets/', contact_views.my_tickets, name='my_tickets'),
    path('tickets/<int:ticket_id>/update/', contact_views.ticket_update, name='ticket_update'),
]
