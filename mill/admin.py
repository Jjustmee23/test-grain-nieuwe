from django.contrib import admin

# Register your models here.
from .models import Device, DeviceData, City, Factory, MQTTData, CountersData

admin.site.register(Device)
admin.site.register(DeviceData)
admin.site.register(CountersData)
admin.site.register(City)
admin.site.register(Factory)
# admin.site.register(MQTTData)
