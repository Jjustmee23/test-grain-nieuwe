from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
# Register your models here.
from .models import (
    Device, Notification, NotificationCategory, ProductionData, City, Factory, 
    UserProfile, Batch, FlourBagCount, Alert, BatchNotification, TVDashboardSettings,
    UserNotificationPreference, EmailTemplate, Microsoft365Settings, NotificationLog,
    EmailHistory, MassMessage, PowerEvent, DevicePowerStatus, PowerNotificationSettings,
    PowerManagementPermission, DoorStatus, DoorOpenLogs, PowerData
)
import requests

admin.site.site_header = 'Mill Admin'
admin.site.site_title = 'Mill Admin'

# Add LogEntry to admin panel
@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message']
    list_filter = ['action_time', 'user', 'content_type', 'action_flag']
    search_fields = ['object_repr', 'change_message']
    date_hierarchy = 'action_time'
    readonly_fields = [field.name for field in LogEntry._meta.fields]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
# Add all fields of Device model to the admin panel.
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status','selected_counter', 'factory', 'created_at')
    list_filter = ('status', 'factory', 'factory__city')  # Added factory__city to enable city filtering
    search_fields = ('id', 'name', 'factory__city__name')  # Added factory__city__name to enable city name searching
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'status', 'factory')
        }),
    )
    readonly_fields = ('created_at',)

# admin.site.register(ProductionData)
@admin.register(ProductionData)
class ProductionDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'daily_production', 'weekly_production', 'monthly_production', 'yearly_production', 'created_at', 'updated_at')
    list_filter = ('device', 'updated_at')
    search_fields = ('device',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('device', 'daily_production', 'weekly_production', 'monthly_production', 'yearly_production')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
# admin.site.register(City)
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'status')
        }),
    )
    readonly_fields = ('created_at',)
# admin.site.register(Factory)
@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'status', 'error','group', 'responsible_users_count', 'created_at')
    list_filter = ('status', 'error', 'city', 'group')
    search_fields = ('name', 'address')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    filter_horizontal = ('responsible_users',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'city', 'status', 'error', 'group')
        }),
        ('Location Information', {
            'fields': ('address', 'latitude', 'longitude'),
            'description': 'Add coordinates for map functionality. You can use Google Maps to find coordinates.'
        }),
        ('Responsible Users', {
            'fields': ('responsible_users',),
            'description': 'Users responsible for this factory. They will receive notifications about power issues and other alerts.'
        }),
    )
    readonly_fields = ('created_at',)
    
    def responsible_users_count(self, obj):
        return obj.responsible_users.count()
    responsible_users_count.short_description = 'Responsible Users'
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'support_tickets_enabled')
    list_filter = ('support_tickets_enabled',)
    filter_horizontal = ('allowed_cities','allowed_factories')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'team')
        }),
        ('Permissions', {
            'fields': ('allowed_cities', 'allowed_factories', 'support_tickets_enabled'),
            'description': 'Support tickets permission is only for super admins'
        }),
    ) 

@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'requires_admin', 'requires_super_admin', 'is_active')
    list_filter = ('notification_type', 'requires_admin', 'requires_super_admin', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

class UserNotificationPreferenceInline(admin.StackedInline):
    model = UserNotificationPreference
    extra = 0
    max_num = 1
    can_delete = False
    fields = (
        'receive_in_app', 'receive_email', 'email_address', 'can_modify_preferences',
        'enabled_categories', 'mandatory_notifications'
    )
    filter_horizontal = ('enabled_categories', 'mandatory_notifications')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    max_num = 1
    can_delete = False
    fields = ('team', 'allowed_cities', 'allowed_factories', 'support_tickets_enabled')
    filter_horizontal = ('allowed_cities', 'allowed_factories')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_in_app', 'receive_email', 'email_address', 'can_modify_preferences', 'is_admin', 'is_super_admin')
    list_filter = ('receive_in_app', 'receive_email', 'can_modify_preferences', 'is_admin', 'is_super_admin')
    search_fields = ('user__username', 'user__email', 'email_address')
    filter_horizontal = ('enabled_categories', 'mandatory_notifications')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'title', 'priority', 'status', 'read', 'created_at')
    list_filter = ('category', 'priority', 'status', 'read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'read_at', 'email_sent_at')

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'subject')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Microsoft365Settings)
class Microsoft365SettingsAdmin(admin.ModelAdmin):
    list_display = ['auth_user', 'from_email', 'from_name', 'is_active', 'has_refresh_token', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['auth_user', 'from_email', 'from_name']
    readonly_fields = ['created_at', 'updated_at', 'has_refresh_token']
    
    fieldsets = (
        ('Azure AD Configuration', {
            'fields': ('client_id', 'client_secret', 'tenant_id')
        }),
        ('Email Configuration', {
            'fields': ('auth_user', 'from_email', 'from_name')
        }),
        ('OAuth2 Status', {
            'fields': ('has_refresh_token', 'token_expires_at', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_refresh_token(self, obj):
        return bool(obj.refresh_token)
    has_refresh_token.boolean = True
    has_refresh_token.short_description = 'Has Refresh Token'
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/oauth2-setup/',
                self.admin_site.admin_view(self.oauth2_setup_view),
                name='mill_microsoft365settings_oauth2_setup',
            ),
            path(
                '<int:object_id>/test-connection/',
                self.admin_site.admin_view(self.test_connection_view),
                name='mill_microsoft365settings_test_connection',
            ),
            path(
                '<int:object_id>/test-email-form/',
                self.admin_site.admin_view(self.test_email_form_view),
                name='mill_microsoft365settings_test_email_form',
            ),
            path(
                '<int:object_id>/test-email/',
                self.admin_site.admin_view(self.test_email_view),
                name='mill_microsoft365settings_test_email',
            ),
            path(
                'auth/callback/',
                self.admin_site.admin_view(self.auth_callback_view),
                name='mill_microsoft365settings_auth_callback',
            ),
        ]
        return custom_urls + urls
    
    def auth_callback_view(self, request):
        """Handle OAuth2 callback from Microsoft"""
        auth_code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            error_description = request.GET.get('error_description', 'Unknown error')
            messages.error(request, f'❌ OAuth2 Error: {error} - {error_description}')
            return HttpResponseRedirect('/super-admin/mill/microsoft365settings/')
        
        if not auth_code:
            messages.error(request, '❌ No authorization code received from Microsoft')
            return HttpResponseRedirect('/super-admin/mill/microsoft365settings/')
        
        # Get the first Microsoft365Settings object (assuming there's only one)
        try:
            settings_obj = Microsoft365Settings.objects.first()
            if not settings_obj:
                messages.error(request, '❌ No Microsoft 365 Settings found')
                return HttpResponseRedirect('/super-admin/mill/microsoft365settings/')
            
            # Exchange authorization code for tokens
            success = self._exchange_auth_code(settings_obj, auth_code)
            if success:
                messages.success(request, '✅ OAuth2 authorization completed successfully!')
            else:
                messages.error(request, '❌ Failed to exchange authorization code')
                
        except Exception as e:
            messages.error(request, f'❌ Error during OAuth2 setup: {str(e)}')
        
        return HttpResponseRedirect('/super-admin/mill/microsoft365settings/')
    
    def oauth2_setup_view(self, request, object_id):
        """OAuth2 setup view"""
        try:
            settings_obj = Microsoft365Settings.objects.get(id=object_id)
            
            # Check if we have an authorization code from the redirect
            auth_code = request.GET.get('code')
            if auth_code:
                # Exchange authorization code for tokens
                success = self._exchange_auth_code(settings_obj, auth_code)
                if success:
                    messages.success(request, '✅ OAuth2 authorization completed successfully!')
                else:
                    messages.error(request, '❌ Failed to exchange authorization code')
                return HttpResponseRedirect('../')
            
            # Check for errors
            error = request.GET.get('error')
            if error:
                error_description = request.GET.get('error_description', 'Unknown error')
                messages.error(request, f'❌ OAuth2 Error: {error} - {error_description}')
                return HttpResponseRedirect('../')
            
            # Generate and redirect to authorization URL
            auth_url = self._generate_auth_url(settings_obj)
            return HttpResponseRedirect(auth_url)
            
        except Microsoft365Settings.DoesNotExist:
            messages.error(request, 'Microsoft 365 Settings not found.')
            return HttpResponseRedirect('../')
    
    def test_email_form_view(self, request, object_id):
        """Show test email form"""
        try:
            settings_obj = Microsoft365Settings.objects.get(id=object_id)
            
            if request.method == 'POST':
                test_email = request.POST.get('test_email')
                if test_email:
                    # Redirect to test email view with the email
                    return HttpResponseRedirect(f'../test-email/')
                else:
                    messages.error(request, 'Please enter an email address.')
            
            # Show the form
            context = {
                'title': 'Send Test Email',
                'settings': settings_obj,
                'opts': self.model._meta,
                'original': settings_obj,
            }
            
            return self.response_change(request, settings_obj)
            
        except Microsoft365Settings.DoesNotExist:
            messages.error(request, 'Microsoft 365 Settings not found.')
            return HttpResponseRedirect('../')
    
    def test_connection_view(self, request, object_id):
        """Test OAuth2 connection"""
        try:
            settings_obj = Microsoft365Settings.objects.get(id=object_id)
            
            from mill.services.simple_email_service import SimpleEmailService
            email_service = SimpleEmailService()
            
            success, message = email_service.test_connection()
            
            if success:
                messages.success(request, f'✅ {message}')
            else:
                messages.error(request, f'❌ {message}')
                
        except Microsoft365Settings.DoesNotExist:
            messages.error(request, 'Microsoft 365 Settings not found.')
        
        return HttpResponseRedirect('../')
    
    def test_email_view(self, request, object_id):
        """Send test email"""
        try:
            settings_obj = Microsoft365Settings.objects.get(id=object_id)
            
            from mill.services.simple_email_service import SimpleEmailService
            email_service = SimpleEmailService()
            
            # Get email from POST data or use current user's email as fallback
            test_email = request.POST.get('test_email') or request.user.email
            if not test_email:
                messages.error(request, 'No email address provided. Please enter an email address.')
                return HttpResponseRedirect('../')
            
            success, message = email_service.test_email_send(test_email)
            
            if success:
                messages.success(request, f'✅ Test email sent successfully to {test_email}!')
            else:
                messages.error(request, f'❌ Failed to send test email: {message}')
                
        except Microsoft365Settings.DoesNotExist:
            messages.error(request, 'Microsoft 365 Settings not found.')
        
        return HttpResponseRedirect('../')
    
    def _generate_auth_url(self, settings_obj):
        """Generate OAuth2 authorization URL"""
        base_url = f"https://login.microsoftonline.com/{settings_obj.tenant_id}/oauth2/v2.0/authorize"
        
        params = {
            'client_id': settings_obj.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:8000/auth/callback',
            'scope': 'https://graph.microsoft.com/Mail.Send offline_access',
            'response_mode': 'query',
            'state': 'oauth2_setup'
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    def _exchange_auth_code(self, settings_obj, auth_code):
        """Exchange authorization code for tokens"""
        try:
            token_url = f"https://login.microsoftonline.com/{settings_obj.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': settings_obj.client_id,
                'client_secret': settings_obj.client_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': 'http://localhost:8000/auth/callback',
                'scope': 'https://graph.microsoft.com/Mail.Send offline_access'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Save tokens
                settings_obj.access_token = token_data['access_token']
                settings_obj.refresh_token = token_data.get('refresh_token', '')
                
                # Calculate expiration
                expires_in = token_data.get('expires_in', 3600)
                from django.utils import timezone
                from datetime import timedelta
                settings_obj.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 300)
                
                settings_obj.save()
                return True
            else:
                return False
                
        except Exception as e:
            return False

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'delivery_method', 'status', 'sent_at')
    list_filter = ('delivery_method', 'status', 'sent_at')
    search_fields = ('notification__title', 'notification__user__username')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at',)

@admin.register(EmailHistory)
class EmailHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_type', 'subject', 'status', 'sent_at', 'sent_by')
    list_filter = ('email_type', 'status', 'sent_at', 'sent_by')
    search_fields = ('user__username', 'user__email', 'subject', 'message')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at', 'opened_at', 'clicked_at')
    date_hierarchy = 'sent_at'
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(MassMessage)
class MassMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'sent_by', 'status', 'total_recipients', 'sent_count', 'failed_count', 'sent_at')
    list_filter = ('status', 'sent_at', 'sent_by')
    search_fields = ('title', 'message', 'subject')
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at', 'total_recipients', 'sent_count', 'failed_count')
    filter_horizontal = ('target_users',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser



@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'factory', 'wheat_amount', 'expected_flour_output', 'actual_flour_output', 'status', 'is_completed', 'created_at')
    list_filter = ('status', 'is_completed', 'factory', 'created_at')
    search_fields = ('batch_number', 'factory__name')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('batch_number', 'factory', 'status', 'is_completed')
        }),
        ('Production Data', {
            'fields': ('wheat_amount', 'waste_factor', 'expected_flour_output', 'actual_flour_output')
        }),
        ('Timestamps', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('expected_flour_output', 'created_at', 'updated_at')

@admin.register(FlourBagCount)
class FlourBagCountAdmin(admin.ModelAdmin):
    list_display = ('batch', 'device', 'bag_count', 'bags_weight', 'timestamp')
    list_filter = ('batch__factory', 'timestamp')
    search_fields = ('batch__batch_number', 'device__name')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('batch', 'alert_type', 'severity', 'is_active', 'is_acknowledged', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_active', 'is_acknowledged', 'created_at')
    search_fields = ('batch__batch_number', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(BatchNotification)
class BatchNotificationAdmin(admin.ModelAdmin):
    list_display = ('batch', 'notification_type', 'sent_at', 'is_read', 'email_sent')
    list_filter = ('notification_type', 'is_read', 'email_sent', 'sent_at')
    search_fields = ('batch__batch_number', 'message')
    date_hierarchy = 'sent_at'
    ordering = ('-sent_at',)
    readonly_fields = ('sent_at',)
    fieldsets = (
        ('Notification Information', {
            'fields': ('batch', 'notification_type', 'message')
        }),
        ('Recipients', {
            'fields': ('sent_to',)
        }),
        ('Status', {
            'fields': ('is_read', 'email_sent')
        }),
        ('Timestamps', {
            'fields': ('sent_at',),
            'classes': ('collapse',)
        }),
    )


# Custom User Admin with Notification Preferences and User Profile
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, UserNotificationPreferenceInline]
    
    def get_inline_instances(self, request, obj=None):
        # Only show inlines when editing existing users
        if obj is None:  # Creating new user
            return []
        return super().get_inline_instances(request, obj)
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/email-management/',
                self.admin_site.admin_view(self.email_management_view),
                name='user-email-management',
            ),
        ]
        return custom_urls + urls
    
    def email_management_view(self, request, user_id):
        from django.shortcuts import render, get_object_or_404
        from django.contrib.auth.models import User
        from mill.models import EmailHistory, EmailTemplate
        from mill.services.simple_email_service import SimpleEmailService
        
        user = get_object_or_404(User, id=user_id)
        email_service = SimpleEmailService()
        
        # Get email history for this user
        email_history = EmailHistory.objects.filter(user=user).order_by('-sent_at')
        
        # Get available email templates
        email_templates = EmailTemplate.objects.filter(is_active=True)
        
        # Handle email sending
        if request.method == 'POST':
            email_type = request.POST.get('email_type')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            template_id = request.POST.get('template_id')
            
            if template_id:
                template = EmailTemplate.objects.get(id=template_id)
                subject = template.subject
                message = template.content
            
            # Send email
            success, response = email_service.send_email(
                user.email,
                subject,
                message,
                email_type=email_type
            )
            
            if success:
                messages.success(request, f'Email successfully sent to {user.email}')
            else:
                messages.error(request, f'Failed to send email: {response}')
            
            return HttpResponseRedirect(request.path)
        
        context = {
            'user': user,
            'email_history': email_history,
            'email_templates': email_templates,
            'title': f'Email Management - {user.username}',
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/mill/user/email_management.html', context)

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(TVDashboardSettings)
class TVDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_mode', 'color_theme', 'refresh_interval', 'is_active', 'created_at')
    list_filter = ('display_mode', 'color_theme', 'refresh_interval', 'is_active', 'created_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'
    ordering = ('-is_active', '-created_at')
    
    fieldsets = (
        ('Basic Settings', {
            'fields': ('name', 'is_active', 'created_by')
        }),
        ('Display Settings', {
            'fields': ('display_mode', 'sort_criteria', 'sort_direction', 'cards_per_row')
        }),
        ('Color Theme Settings', {
            'fields': ('color_theme', 'primary_color', 'secondary_color', 'accent_color', 'success_color', 'warning_color', 'danger_color'),
            'classes': ('collapse',)
        }),
        ('Font Settings', {
            'fields': ('font_family', 'font_size_base', 'font_size_large', 'font_size_xlarge', 'font_weight'),
            'classes': ('collapse',)
        }),
        ('Background Settings', {
            'fields': ('background_style', 'background_color', 'background_image_url'),
            'classes': ('collapse',)
        }),
        ('Card Styling', {
            'fields': ('card_border_radius', 'card_shadow', 'card_transparency', 'card_border_width'),
            'classes': ('collapse',)
        }),
        ('Animation Settings', {
            'fields': ('animation_speed', 'hover_effects', 'transition_effects'),
            'classes': ('collapse',)
        }),
        ('Layout Settings', {
            'fields': ('show_city_headers', 'card_spacing', 'section_padding'),
            'classes': ('collapse',)
        }),
        ('Progress Indicators', {
            'fields': ('show_progress_bars', 'progress_style', 'progress_animation'),
            'classes': ('collapse',)
        }),
        ('Alert Styling', {
            'fields': ('show_alerts', 'alert_position', 'alert_duration'),
            'classes': ('collapse',)
        }),
        ('Filter Settings', {
            'fields': ('selected_cities', 'selected_factories', 'show_only_active'),
            'classes': ('collapse',)
        }),
        ('Visual Settings', {
            'fields': ('show_summary_stats', 'show_factory_status', 'show_time_info'),
            'classes': ('collapse',)
        }),
        ('Additional Visual Toggles', {
            'fields': (
                'show_production_charts', 'show_performance_metrics', 'show_alert_notifications', 'show_system_status',
                'show_weather_info', 'show_clock_display', 'show_production_targets', 'show_efficiency_ratios',
                'show_quality_metrics', 'show_maintenance_status', 'show_energy_consumption', 'show_temperature_readings',
                'show_humidity_levels', 'show_pressure_readings', 'show_vibration_data', 'show_door_status',
                'show_power_consumption', 'show_network_status', 'show_device_health', 'show_batch_information',
                'show_shift_information', 'show_operator_info', 'show_safety_alerts', 'show_maintenance_alerts',
                'show_quality_alerts', 'show_production_alerts', 'show_system_alerts'
            ),
            'classes': ('collapse',)
        }),
        ('Auto-refresh and Animation', {
            'fields': ('refresh_interval', 'auto_scroll', 'scroll_speed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('selected_cities', 'selected_factories')
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(DoorStatus)
class DoorStatusAdmin(admin.ModelAdmin):
    list_display = ('device', 'is_open', 'status_display', 'last_check', 'door_input_index')
    list_filter = ('is_open', 'last_check', 'device__factory')
    search_fields = ('device__name', 'device__factory__name')
    ordering = ('-last_check',)
    readonly_fields = ('created_at', 'updated_at', 'last_check')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device', 'door_input_index')
        }),
        ('Door Status', {
            'fields': ('is_open', 'last_din_data')
        }),
        ('Timestamps', {
            'fields': ('last_check', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(DoorOpenLogs)
class DoorOpenLogsAdmin(admin.ModelAdmin):
    list_display = ('device', 'timestamp', 'din_data', 'door_input_index', 'is_resolved', 'resolved_by', 'resolved_at')
    list_filter = ('is_resolved', 'timestamp', 'device__factory', 'door_input_index')
    search_fields = ('device__name', 'device__factory__name', 'din_data')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device', 'door_input_index')
        }),
        ('Door Event', {
            'fields': ('din_data', 'timestamp')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        """Show only active config or all if user is superuser"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_active=True)


# Power Management Admin Classes
@admin.register(PowerEvent)
class PowerEventAdmin(admin.ModelAdmin):
    list_display = ('device', 'event_type', 'severity', 'is_resolved', 'created_at', 'ain1_value')
    list_filter = ('event_type', 'severity', 'is_resolved', 'created_at', 'device__factory')
    search_fields = ('device__name', 'message', 'device__factory__name')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'notification_sent', 'email_sent', 'super_admin_notified')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('device', 'event_type', 'severity', 'message')
        }),
        ('Power Data', {
            'fields': ('ain1_value', 'previous_ain1_value'),
            'classes': ('collapse',)
        }),
        ('Production Data', {
            'fields': ('counter_1_value', 'counter_2_value', 'counter_3_value', 'counter_4_value'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('Notification Status', {
            'fields': ('notification_sent', 'email_sent', 'super_admin_notified'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DevicePowerStatus)
class DevicePowerStatusAdmin(admin.ModelAdmin):
    list_display = ('device', 'has_power', 'ain1_value', 'last_power_check', 'power_threshold')
    list_filter = ('has_power', 'last_power_check', 'device__factory')
    search_fields = ('device__name', 'device__factory__name')
    ordering = ('-last_power_check',)
    readonly_fields = ('created_at', 'updated_at', 'last_power_check')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device', 'has_power')
        }),
        ('Power Data', {
            'fields': ('ain1_value', 'power_threshold', 'last_power_check')
        }),
        ('Power Events', {
            'fields': ('power_loss_detected_at', 'power_restored_at'),
            'classes': ('collapse',)
        }),
        ('Production Tracking', {
            'fields': ('production_during_power_loss', 'last_production_check'),
            'classes': ('collapse',)
        }),
        ('Notification Settings', {
            'fields': ('notify_on_power_loss', 'notify_on_power_restore', 'notify_on_production_without_power'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PowerNotificationSettings)
class PowerNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'notify_power_loss', 'notify_power_restore', 'notification_frequency')
    list_filter = ('notify_power_loss', 'notify_power_restore', 'notify_production_without_power', 'notification_frequency')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('responsible_devices',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('In-App Notifications', {
            'fields': ('notify_power_loss', 'notify_power_restore', 'notify_production_without_power', 'notify_power_fluctuation')
        }),
        ('Email Notifications', {
            'fields': ('email_power_loss', 'email_power_restore', 'email_production_without_power', 'email_power_fluctuation')
        }),
        ('Device Assignment', {
            'fields': ('responsible_devices',)
        }),
        ('Settings', {
            'fields': ('notification_frequency',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PowerManagementPermission)
class PowerManagementPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_access_power_management', 'can_view_power_status', 'can_resolve_power_events', 'granted_at')
    list_filter = ('can_access_power_management', 'can_view_power_status', 'can_resolve_power_events', 'granted_at')
    search_fields = ('user__username', 'user__email', 'granted_by__username')
    readonly_fields = ('granted_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'granted_by')
        }),
        ('Permissions', {
            'fields': ('can_access_power_management', 'can_view_power_status', 'can_resolve_power_events')
        }),
        ('Additional Information', {
            'fields': ('notes', 'granted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PowerData)
class PowerDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'has_power', 'ain1_value', 'power_loss_count_today', 'power_restore_count_today', 'last_mqtt_update')
    list_filter = ('has_power', 'last_mqtt_update', 'device__factory')
    search_fields = ('device__name', 'device__factory__name')
    ordering = ('-last_mqtt_update',)
    readonly_fields = ('created_at', 'updated_at', 'last_mqtt_update')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device', 'has_power', 'power_threshold')
        }),
        ('Power Values', {
            'fields': ('ain1_value', 'ain2_value', 'ain3_value', 'ain4_value')
        }),
        ('Today Statistics', {
            'fields': ('power_loss_count_today', 'power_restore_count_today', 'total_power_loss_time_today', 
                      'avg_power_consumption_today', 'peak_power_consumption_today', 'total_power_consumption_today')
        }),
        ('Weekly Statistics', {
            'fields': ('power_loss_count_week', 'power_restore_count_week', 'total_power_loss_time_week')
        }),
        ('Monthly Statistics', {
            'fields': ('power_loss_count_month', 'power_restore_count_month', 'total_power_loss_time_month')
        }),
        ('Yearly Statistics', {
            'fields': ('power_loss_count_year', 'power_restore_count_year', 'total_power_loss_time_year')
        }),
        ('Power Events', {
            'fields': ('last_power_loss', 'last_power_restore')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_mqtt_update'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# PowerData is already registered with @admin.register decorator
