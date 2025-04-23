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
from django.db import models

class RawData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='raw_data')
    timestamp = models.DateTimeField(null=True, blank=True)
    mobile_signal = models.IntegerField(null=True, blank=True)
    dout_enabled = models.CharField(max_length=255, null=True, blank=True)
    dout = models.CharField(max_length=255, null=True, blank=True)
    di_mode = models.CharField(max_length=255, null=True, blank=True)
    din = models.CharField(max_length=255, null=True, blank=True)
    counter_1 = models.IntegerField(null=True, blank=True)
    counter_2 = models.IntegerField(null=True, blank=True)
    counter_3 = models.IntegerField(null=True, blank=True)
    counter_4 = models.IntegerField(null=True, blank=True)
    ain_mode = models.CharField(max_length=255, null=True, blank=True)
    ain1_value = models.FloatField(null=True, blank=True)
    ain2_value = models.FloatField(null=True, blank=True)
    ain3_value = models.FloatField(null=True, blank=True)
    ain4_value = models.FloatField(null=True, blank=True)
    ain5_value = models.FloatField(null=True, blank=True)
    ain6_value = models.FloatField(null=True, blank=True)
    ain7_value = models.FloatField(null=True, blank=True)
    ain8_value = models.FloatField(null=True, blank=True)
    start_flag = models.IntegerField(null=True, blank=True)
    type = models.IntegerField(null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)
    end_flag = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.device} - {self.timestamp}"
    
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

        
class ContactTicket(models.Model):
    TICKET_TYPES = [
        ('TECHNICAL', 'Technical Support'),
        ('ACCOUNT', 'Account Issues'),
        ('FEATURE', 'Feature Request'),
        ('BUG', 'Bug Report'),
        ('OTHER', 'Other Inquiry'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING', 'Pending User Response'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Ticket Details
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='NEW')
    
    # Relations
    factory = models.ForeignKey(Factory, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='submitted_tickets'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tickets'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']  # Note: You had '-timestamp' but the field is 'created_at'
        verbose_name = 'Contact Ticket'
        verbose_name_plural = 'Contact Tickets'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['ticket_type', 'status']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.ticket_type} - {self.subject} ({self.status})"
    
    def get_status_display_class(self):
        """Returns Bootstrap class for status badge"""
        return {
            'NEW': 'bg-primary',
            'IN_PROGRESS': 'bg-warning',
            'PENDING': 'bg-info',
            'RESOLVED': 'bg-success',
            'CLOSED': 'bg-secondary',
        }.get(self.status, 'bg-secondary')
    
    def get_priority_display_class(self):
        """Returns Bootstrap class for priority badge"""
        return {
            'LOW': 'bg-success',
            'MEDIUM': 'bg-info',
            'HIGH': 'bg-warning',
            'URGENT': 'bg-danger',
        }.get(self.priority, 'bg-secondary')
    
    @property
    def is_closed(self):
        """Check if the ticket is closed"""
        return self.status in ['RESOLVED', 'CLOSED']
    
    @property
    def resolution_time(self):
        """Calculate the time taken to resolve the ticket"""
        if self.is_closed and self.updated_at and self.created_at:
            return self.updated_at - self.created_at
        return None