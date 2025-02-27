from django.db import models
from django.contrib.auth.models import User

from django.conf import settings

# City model
class City(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Factory model
class Factory(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='factories')
    status = models.BooleanField(default=True)
    error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Device model
class Device(models.Model):
    id = models.CharField(max_length=30,primary_key=True,unique=True)
    name = models.CharField(max_length=255)
    selected_counter = models.CharField(max_length=50, default='counter_1')
    status = models.BooleanField(default=False)
    factory = models.ForeignKey(Factory, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ProductionData model to update hourly, daily, weekly, monthly, and yearly production
class ProductionData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='production_data')
    daily_production = models.IntegerField(default=0)
    weekly_production = models.IntegerField(default=0)
    monthly_production = models.IntegerField(default=0)
    yearly_production = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=['device', 'created_at']),
        ]
    def __str__(self):
        return f"Production Data for {self.device.name} at {self.updated_at}"

# TransactionData model to transactioning hourly, daily, weekly, monthly, and yearly production
class TransactionData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='transaction_data')
    daily_production = models.IntegerField(default=0)
    weekly_production = models.IntegerField(default=0)
    monthly_production = models.IntegerField(default=0)
    yearly_production = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [
            models.Index(fields=['device', 'created_at']),
        ]
    def __str__(self):
        return f"Production Data for {self.device.name} at {self.created_at}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.CharField(max_length=100, blank=True, null=True)
    # Only for non-super_admin users (admins and public_users)
    allowed_cities = models.ManyToManyField(City, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
    # Only for super_admin users
class BatchForFactory(models.Model):
    batchInteger = models.IntegerField()
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='batch_for_factory')
    amountofwheat = models.IntegerField(default=0)
    DateTimeField = models.DateTimeField(auto_now_add=True)
    waistfactor = models.IntegerField(default=20)
    def __str__(self):
        return f"Batch for {self.factory.name} at {self.DateTimeFieldField}"