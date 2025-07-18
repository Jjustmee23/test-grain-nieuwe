from django.contrib import admin
from django.contrib.admin.models import LogEntry
# Register your models here.
from .models import Device, Notification, NotificationCategory, ProductionData, City, Factory, UserProfile, Batch, FlourBagCount, Alert, BatchNotification, TVDashboardSettings

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
    list_display = ('name', 'city', 'status', 'error','group', 'created_at')
    list_filter = ('status', 'error', 'city', 'group')
    search_fields = ('name', 'address')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'city', 'status', 'error', 'group')
        }),
        ('Location Information', {
            'fields': ('address', 'latitude', 'longitude'),
            'description': 'Add coordinates for map functionality. You can use Google Maps to find coordinates.'
        }),
    )
    readonly_fields = ('created_at',)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('allowed_cities','allowed_factories') 

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'message', 'read', 'timestamp')
    list_filter = ('category', 'read', 'timestamp')
    search_fields = ('user', 'message')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    fieldsets = (
        (None, {
            'fields': ('user', 'category', 'message', 'read', 'timestamp')
        }),
    )
    readonly_fields = ('timestamp',)

@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name','description')
    search_fields = ('name','description')

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
    
    def get_queryset(self, request):
        """Show only active config or all if user is superuser"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_active=True)
