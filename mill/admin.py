from django.contrib import admin
from django.contrib.admin.models import LogEntry
# Register your models here.
from .models import Device, Notification, NotificationCategory, ProductionData, City, Factory, UserProfile

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
    search_fields = ('name',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'city', 'status', 'error')
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
