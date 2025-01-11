from django.contrib import admin

# Register your models here.
from .models import Device, ProductionData, City, Factory, UserProfile

admin.site.site_header = 'Mill Admin'
admin.site.site_title = 'Mill Admin'
admin.site.register(Device)
admin.site.register(ProductionData)
admin.site.register(City)
admin.site.register(Factory)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('allowed_cities',) 