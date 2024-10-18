from django.db import models

class City(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Factory(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, related_name='factories')
    status = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f" {self.name} at {self.created_at}"

class Device(models.Model):
    name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, unique=True)
    selected_counter = models.CharField(max_length=50, default='counter_1')
    status = models.BooleanField(default=False)
    factory = models.ForeignKey('Factory', on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name or self.serial_number

# Devicedata are transections of each device wich will be added daily and not updated or deleted
class DeviceData(models.Model):
    device = models.ForeignKey(Device, null=True, on_delete=models.SET_NULL,db_index=True)
    daily_total = models.IntegerField(default=0)
    weekly_total = models.IntegerField(default=0)
    monthly_total = models.IntegerField(default=0)
    yearly_total = models.IntegerField(default=0)
    reference = models.CharField(max_length=255)    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Data for {self.device.name} at {self.created_at}"

# CounterData values will be created every 30 minutes by MQTT. They will come from another DB 
class CountersData(models.Model):
    device = models.ForeignKey(Device,null=True, on_delete = models.SET_NULL,db_index=True)
    counter_1 = models.IntegerField(default=0)
    counter_2 = models.IntegerField(default=0)
    counter_3 = models.IntegerField(default=0)
    counter_4 = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Counters Data for {self.device.name} at {self.created_at}"
    
class MQTTData(models.Model):
    device_id = models.CharField(max_length=255)
    counter = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'mqtt_data'
        ordering = ['-created_at']
