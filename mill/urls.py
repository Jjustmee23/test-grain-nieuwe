
from django.urls import path
from .views import index, manage_admin_view

urlpatterns = [
    path('', index, name='index'),
    path('manage-admin/', manage_admin_view, name='manage_admin'),
]
