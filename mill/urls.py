
from django.urls import path, include
from django.contrib import admin
from .views_new import testmill
# from mill. import profile_views
from mill import views, apis
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('/', views.index, name='index'),
    path('manage-admin/', views.manage_admin_view, name='manage_admin'),
    path('test/', testmill, name='mill'),

    # Batch URLs
    path('batches/', views.BatchListView.as_view(), name='batch-list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch-create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch-detail'),
    path('batches/<int:pk>/update/', views.BatchUpdateView.as_view(), name='batch-update'),
    
    # Sensor URLs
    path('sensor/data/', views.sensor_data_receiver, name='sensor-data'),
    path('sensor/status/<str:device_id>/', views.sensor_status, name='sensor-status'),
    
    # Analytics URLs
    path('analytics/', views.analytics_dashboard, name='analytics-dashboard'),
    path('analytics/batch/<int:batch_id>/', views.batch_performance, name='batch-performance'),
    
    # Alert URLs
    path('alerts/', views.AlertListView.as_view(), name='alert-list'),
    path('alerts/dashboard/', views.alert_dashboard, name='alert-dashboard'),
    path('alerts/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge-alert'),
    # path('admin/',admin.site.urls,name='admin'),
    path('admin/', views.admin_view, name='admin'),
    path('super-admin/', admin.site.urls),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/manage/', views.manage_profile, name='manage_profile'),


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
    path('export-data/', views.export_data, name='export_data'),
    path('preview-data/', views.preview_data, name='preview_data'),


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

    # Notifications Urls
    # path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    # path('notifications/create/', views.NotificationCreateView.as_view(), name='notification-create'),
    # path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    # path('notifications/<int:pk>/update/', views.NotificationUpdateView.as_view(), name='notification-update'),

    # API endpoints
    path('api/available-devices/', views.api_get_available_devices, name='api_get_available_devices'),
    path('api/factory-devices/<int:factory_id>/', views.api_get_factory_devices, name='api_get_factory_devices'),

    path('api/chart_data/', apis.chart_data, name='chart_data'),
    path('api/devices/',apis.get_devices,name='get-devices'),
    path('resolve-door-alert/<int:log_id>/', views.resolve_door_alert, name='resolve_door_alert'),
    



    path('contact/', views.contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('tickets/', views.my_tickets, name='my_tickets'),
    path('tickets/<int:ticket_id>/update/', views.ticket_update, name='ticket_update'),
    

]