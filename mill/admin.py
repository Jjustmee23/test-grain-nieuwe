from django.contrib import admin

# Register your models here.
from .models import Device, ProductionData, City, Factory

admin.site.register(Device)
admin.site.register(ProductionData)
admin.site.register(City)
admin.site.register(Factory)
