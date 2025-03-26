from django.contrib import admin
from django.urls import path, include
from mill import views, apis
from django.conf.urls import handler404
from django.contrib.auth import views as auth_views
# from mill. import profile_views

from mill.views import (
    BatchListView, BatchCreateView, BatchUpdateView, BatchDetailView,
    sensor_data_receiver, sensor_status,
    analytics_dashboard, batch_performance,
    AlertListView, alert_dashboard, acknowledge_alert, profile_views
)

urlpatterns = [
    # Batch URLs
    path('batches/', BatchListView.as_view(), name='batch-list'),
    path('batches/create/', BatchCreateView.as_view(), name='batch-create'),
    path('batches/<int:pk>/', BatchDetailView.as_view(), name='batch-detail'),
    path('batches/<int:pk>/update/', BatchUpdateView.as_view(), name='batch-update'),
    
    # Sensor URLs
    path('sensor/data/', sensor_data_receiver, name='sensor-data'),
    path('sensor/status/<str:device_id>/', sensor_status, name='sensor-status'),
    
    # Analytics URLs
    path('analytics/', analytics_dashboard, name='analytics-dashboard'),
    path('analytics/batch/<int:batch_id>/', batch_performance, name='batch-performance'),
    
    # Alert URLs
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/dashboard/', alert_dashboard, name='alert-dashboard'),
    path('alerts/<int:alert_id>/acknowledge/', acknowledge_alert, name='acknowledge-alert'),
    # path('admin/',admin.site.urls,name='admin'),
    path('admin/', views.admin_view, name='admin'),
    path('super-admin/', admin.site.urls),
    path('', include('mill.urls')),  # Include the mill app URLs
    path('change-password/', views.change_password, name='change_password'),
    path('profile/manage/', profile_views.manage_profile, name='manage_profile'),


    # Authentication
    # path('login/', auth_views.LoginView.as_view(template_name='mill/login.html'), name='login'),
    path('login/',views.BasicLoginView.as_view(),name='login'),
    path('logout/', views.BasicLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # User management
    path('profile/', views.profile, name='profile'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('create-user/', views.create_user, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('assign-rights/<int:user_id>/', views.assign_rights, name='assign_rights'),

    # Views
    path('', views.index, name='index'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('view-statistics/<int:factory_id>/', views.view_statistics, name='view_statistics'),
    path('view-tables/', views.view_tables, name='view_tables'),

    # Management
    path('manage-databases/', views.manage_databases, name='manage_databases'),
    path('manage-devices/', views.manage_devices, name='manage_devices'),
    path('manage-tables/', views.manage_tables, name='manage_tables'),
    path('manage-factory/', views.manage_factory, name='manage_factory'),
    # path('manage-batch/', views.manage_batches, name='manage_batches'),
    path('manage-city/', views.manage_city, name='manage_city'),

    # Device operations
    path('pair-device/', views.pair_device, name='pair_device'),
    path('add-device/', views.add_device, name='add_device'),
    path('toggle-device-status/', views.toggle_device_status, name='toggle_device_status'),
    path('remove-device/', views.remove_device, name='remove_device'),

    # Data operations
    path('download-factories/', views.download_factories, name='download_factories'),
    path('upload-factories/', views.upload_factories, name='upload_factories'),
    path('download-cities/', views.download_cities, name='download_cities'),
    path('upload-cities/', views.upload_cities, name='upload_cities'),
    path('download-devices/', views.download_devices, name='download_devices'),
    path('upload-devices/', views.upload_devices, name='upload_devices'),

    # API endpoints
    path('api/available-devices/', views.api_get_available_devices, name='api_get_available_devices'),
    path('api/factory-devices/<int:factory_id>/', views.api_get_factory_devices, name='api_get_factory_devices'),

    path('api/chart_data/', apis.chart_data, name='chart_data'),
    path('api/devices/',apis.get_devices,name='get-devices'),

    # Include mill URLs
    path('', include('mill.urls')),
]

handler404 = 'mill.views.custom_404_view'