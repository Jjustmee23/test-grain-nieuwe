
from django.urls import path, include
from django.contrib import admin
# from mill. import profile_views
from mill import views, apis
from mill.views import tv_dashboard_views, factory_map_views, notification_api_views, power_management_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('manage-admin/', views.manage_admin_view, name='manage_admin'),

    # OAuth2 callback URL
    path('auth/callback/', views.auth_callback, name='auth_callback'),

    # Batch URLs
    path('batches/', views.BatchListView.as_view(), name='batch-list'),
    path('batches/create/', views.BatchCreateView.as_view(), name='batch-create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch-detail'),
    path('batches/<int:pk>/update/', views.BatchUpdateView.as_view(), name='batch-update'),
    path('batches/<int:pk>/manage/', views.BatchManagementView.as_view(), name='batch-manage'),
    path('batches/<int:pk>/counter/', views.BatchCounterUpdateView.as_view(), name='batch-counter'),
    path('batches/<int:pk>/auto-update/', views.BatchAutoUpdateView.as_view(), name='batch-auto-update'),
    path('api/batch/<int:batch_id>/chart-data/', views.batch_chart_data, name='batch_chart_data'),
    path('api/batch-notifications/', views.BatchNotificationView.as_view(), name='batch-notifications'),
    
    # Sensor URLs
    path('sensor/data/', views.sensor_data_receiver, name='sensor-data'),
    path('sensor/status/<str:device_id>/', views.sensor_status, name='sensor-status'),
    path('mqtt/data/', views.mqtt_data_receiver, name='mqtt-data'),
    
    # Power Management URLs
    path('power-dashboard/', power_management_views.power_dashboard, name='power_dashboard'),
    path('power-events/', power_management_views.power_events_list, name='power_events_list'),
    path('power-events/<int:event_id>/', power_management_views.power_event_detail, name='power_event_detail'),
    path('power-events/<int:event_id>/resolve/', power_management_views.resolve_power_event, name='resolve_power_event'),
    path('device-power-status/<str:device_id>/', power_management_views.device_power_status, name='device_power_status'),
    path('power-notification-settings/', power_management_views.power_notification_settings, name='power_notification_settings'),
    path('power-analytics/', power_management_views.power_analytics, name='power_analytics'),
    path('api/power-status/<int:factory_id>/', power_management_views.power_status_api, name='power_status_api'),
    path('api/power-data-mqtt/<int:factory_id>/', power_management_views.power_data_mqtt_api, name='power_data_mqtt_api'),
    path('sync-counter-data/', power_management_views.sync_counter_data, name='sync_counter_data'),
    
    # Factory-specific power management URLs
    path('factory/<int:factory_id>/power-events/', power_management_views.factory_power_events, name='factory_power_events'),
    path('factory/<int:factory_id>/power-analytics/', power_management_views.factory_power_analytics, name='factory_power_analytics'),
    path('factory/<int:factory_id>/power-overview/', power_management_views.factory_power_overview, name='factory_power_overview'),
    
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
    
    # Notification management URLs
    path('notification-management/', views.notification_management, name='notification_management'),
    path('send-notification/', views.send_notification, name='send_notification'),
    path('update-user-preferences/<int:user_id>/', views.update_user_notification_preferences, name='update_user_preferences'),
    path('microsoft365-settings/', views.microsoft365_settings, name='microsoft365_settings'),
    path('test-email-connection/', views.test_email_connection, name='test_email_connection'),
    path('test-email-send/', views.test_email_send, name='test_email_send'),
    
    # Email management URLs
    path('email-history/', views.email_history, name='email_history'),
    path('user-email-history/<int:user_id>/', views.user_email_history, name='user_email_history'),
    path('user-email-management/<int:user_id>/', views.user_email_management, name='user_email_management'),
    path('send-direct-email/<int:user_id>/', views.send_direct_email, name='send_direct_email'),
    path('mass-messaging/', views.mass_messaging, name='mass_messaging'),
    path('email-templates/', views.email_templates, name='email_templates'),
    path('send-welcome-email/<int:user_id>/', views.send_welcome_email, name='send_welcome_email'),
    path('send-password-reset-email/<int:user_id>/', views.send_password_reset_email, name='send_password_reset_email'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/manage/', views.manage_profile, name='manage_profile'),
    
    # Two-Factor Authentication URLs
    path('profile/setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('profile/2fa-status/', views.get_2fa_status, name='get_2fa_status'),


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
    path('tv-dashboard/', views.tv_dashboard, name='tv-dashboard'),

    path('view-statistics/<int:factory_id>/', views.view_statistics, name='view_statistics'),
    path('api/device-chart-data/<int:factory_id>/', views.get_device_chart_data, name='get_device_chart_data'),
    path('api/door-status/<int:factory_id>/', views.get_door_status_data, name='get_door_status_data'),
    path('api/power-status/<int:factory_id>/', views.get_power_status_data, name='get_power_status_data'),
    path('api/power-data-mqtt/<int:factory_id>/', views.get_power_data_from_mqtt, name='get_power_data_from_mqtt'),
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
    path('feedback/create/', views.create_feedback, name='create_feedback'),
    path('feedback/list/', views.feedback_list, name='feedback_list'),


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

    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    # path('notifications/create/', views.NotificationCreateView.as_view(), name='notification-create'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),

    # Notification API endpoints
    path('api/notifications/send/', views.notification_api_views.SendNotificationView.as_view(), name='api_send_notification'),
    path('api/user/preferences/', views.notification_api_views.UserPreferencesView.as_view(), name='api_user_preferences'),
    path('api/user/notifications/', views.notification_api_views.UserNotificationsView.as_view(), name='api_user_notifications'),
    path('api/admin/notifications/', views.notification_api_views.AdminNotificationManagementView.as_view(), name='api_admin_notifications'),
    path('api/notifications/stats/', views.notification_api_views.NotificationStatsView.as_view(), name='api_notification_stats'),

    # path('notifications/<int:pk>/update/', views.NotificationUpdateView.as_view(), name='notification-update'),

    # API endpoints
    path('api/available-devices/', views.api_get_available_devices, name='api_get_available_devices'),
    path('api/factory-devices/<int:factory_id>/', views.api_get_factory_devices, name='api_get_factory_devices'),

    path('api/chart_data/', apis.chart_data, name='chart_data'),
    path('api/batch_chart_data/', apis.batch_chart_data, name='batch_chart_data'),
    path('api/cities/<int:city_id>/factories/', apis.get_city_factories, name='get_city_factories'),

    path('api/devices/',apis.get_devices,name='get-devices'),
    path('resolve-door-alert/<int:log_id>/', views.resolve_door_alert, name='resolve_door_alert'),
    



    # Contact and Ticket URLs
    path('contact/', views.contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    
    # Legal URLs
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    
    # User Ticket URLs
    path('tickets/', views.my_tickets, name='my_tickets'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/update/', views.ticket_update, name='ticket_update'),
    
    # Admin Ticket URLs
    path('admin/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin/tickets/<int:ticket_id>/', views.admin_ticket_detail, name='admin_ticket_detail'),
    path('admin/tickets/<int:ticket_id>/status-update/', views.admin_ticket_status_update, name='admin_ticket_status_update'),
    path('admin/tickets/search-users/', views.admin_search_users, name='admin_search_users'),
    path('admin/tickets/create/', views.admin_create_ticket, name='admin_create_ticket'),
    path('admin/tickets/<int:ticket_id>/quick-reply/', views.admin_quick_reply, name='admin_quick_reply'),
    path('admin/tickets/<int:ticket_id>/assign/', views.admin_assign_ticket, name='admin_assign_ticket'),
    path('admin/tickets/<int:ticket_id>/transfer/', views.admin_transfer_ticket, name='admin_transfer_ticket'),
    path('admin/tickets/<int:ticket_id>/delete/', views.admin_delete_ticket, name='admin_delete_ticket'),
    


    path('api/devices/',apis.get_devices,name='get-devices'),

    # TV Dashboard Settings URLs
    path('tv-dashboard-settings/', tv_dashboard_views.tv_dashboard_settings_list, name='tv_dashboard_settings_list'),
    path('tv-dashboard-settings/create/', tv_dashboard_views.tv_dashboard_settings_create, name='tv_dashboard_settings_create'),
    path('tv-dashboard-settings/<int:setting_id>/edit/', tv_dashboard_views.tv_dashboard_settings_edit, name='tv_dashboard_settings_edit'),
    path('tv-dashboard-settings/<int:setting_id>/delete/', tv_dashboard_views.tv_dashboard_settings_delete, name='tv_dashboard_settings_delete'),
    path('tv-dashboard-settings/<int:setting_id>/activate/', tv_dashboard_views.tv_dashboard_settings_activate, name='tv_dashboard_settings_activate'),
    path('tv-dashboard-settings/<int:setting_id>/preview/', tv_dashboard_views.tv_dashboard_settings_preview, name='tv_dashboard_settings_preview'),
    path('tv-dashboard-settings/<int:setting_id>/duplicate/', tv_dashboard_views.tv_dashboard_settings_duplicate, name='tv_dashboard_settings_duplicate'),

    # Factory Map URLs
    path('factory-map/', factory_map_views.factory_map, name='factory_map'),
    path('api/factory-map-data/', factory_map_views.factory_map_data, name='factory_map_data'),

]

