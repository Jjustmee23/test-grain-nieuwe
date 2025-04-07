from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone


# City model
class City(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Factory model
class Factory(models.Model):
    GROUP_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('commercial', 'Commercial')
    ]
    
    name = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='factories')
    status = models.BooleanField(default=True)
    error = models.BooleanField(default=False)
    group = models.CharField(max_length=30, choices=GROUP_CHOICES, default='public')
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
    allowed_factories = models.ManyToManyField(Factory, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Batch(models.Model):
    batch_number = models.CharField(max_length=50, unique=True)
    factory = models.ForeignKey(Factory, on_delete=models.SET_NULL, null=True, related_name='batches')
    wheat_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text="Amount of wheat in tons"
    )
    waste_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.0,  # Default 20% waste factor
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Waste factor percentage"
    )
    expected_flour_output = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.0)],
        help_text="Expected flour output in tons"
    )
    actual_flour_output = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Actual flour output in tons"
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate expected flour output based on wheat amount and waste factor
        if not self.expected_flour_output:
            self.expected_flour_output = self.wheat_amount * ((100 - self.waste_factor) / 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Batch {self.batch_number} - {self.factory.name}"

class FlourBagCount(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='flour_bag_counts')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='flour_bag_counts')
    bag_count = models.IntegerField(default=0)
    bags_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Total weight of bags in tons"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flour_bag_counts'
    )

    class Meta:
        indexes = [
            models.Index(fields=['batch', 'device', 'timestamp']),
        ]

    def __str__(self):
        return f"Bag Count for Batch {self.batch.batch_number} - {self.bag_count} bags"

class Alert(models.Model):
    ALERT_TYPES = [
        ('PRODUCTION_LOW', 'Production Below Target'),
        ('DEVIATION', 'High Deviation from Expected'),
        ('SYSTEM', 'System Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='acknowledged_alerts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch', 'alert_type', 'created_at']),
        ]

    def __str__(self):
        return f"Alert: {self.alert_type} for Batch {self.batch.batch_number}"

# models.py
from django.db import models
from django.contrib.auth.models import User

class NotificationCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name

class UserNotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enabled_category = models.ManyToManyField(NotificationCategory, blank=True)
    receive_in_app = models.BooleanField(default=True)
    receive_email = models.BooleanField(default=False)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.category}: {self.message}"

    class Meta:
        ordering = ['-timestamp']