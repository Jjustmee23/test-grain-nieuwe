from django.db import models
from django.utils import timezone
from datetime import timedelta

class Device(models.Model):
    name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, unique=True)
    selected_counter = models.CharField(max_length=50, default='counter_1')
    status = models.BooleanField(default=False)
    factory = models.ForeignKey('Factory', on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    
    def __str__(self):
        return self.name or self.serial_number

class DeviceData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    counter_1 = models.IntegerField(default=0)
    counter_2 = models.IntegerField(default=0)
    counter_3 = models.IntegerField(default=0)
    counter_4 = models.IntegerField(default=0)
    daily_total = models.IntegerField(default=0)
    weekly_total = models.IntegerField(default=0)
    monthly_total = models.IntegerField(default=0)
    yearly_total = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Data for {self.device.name} at {self.created_at}"

class City(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Factory(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.BooleanField(default=False)
    dailyTotal = models.IntegerField(default=0)
    error = models.BooleanField(default=False)
    last_update = models.DateTimeField(default=timezone.now)
    
    def check_status(self):
        if self.last_update and timezone.now() - self.last_update > timedelta(minutes=5):
            self.error = True
            self.status = False
        else:
            self.error = False
            self.status = True
        self.save()

class MQTTData(models.Model):
    device_id = models.CharField(max_length=255)
    counter = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mqtt_data'
        ordering = ['-created_at']
