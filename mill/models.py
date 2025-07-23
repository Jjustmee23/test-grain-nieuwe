from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from decimal import Decimal


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
        ('Public', 'Public'),
        ('private', 'Private'),
        ('commercial', 'Commercial')
    ]
    
    name = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='factories')
    status = models.BooleanField(default=True)
    error = models.BooleanField(default=False)
    group = models.CharField(max_length=30, choices=GROUP_CHOICES, default='Public')
    
    # Address fields for map functionality
    address = models.TextField(blank=True, null=True, help_text="Full address of the factory")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude coordinate")
    
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
    # Support tickets permission for super admins
    support_tickets_enabled = models.BooleanField(default=False, help_text="Enable support tickets management for this user")

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
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    start_value = models.IntegerField(default=0, help_text="Starting counter value from latest transaction")
    current_value = models.IntegerField(default=0, help_text="Current counter value")
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('in_process', 'In Process'),
        ('paused', 'Paused'),
        ('stopped', 'Stopped'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_completed = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_batches'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            # For new batches, start_value should always be 0
            # The current_value will be the difference since batch start
            self.start_value = 0
                
        # Calculate expected flour output based on wheat amount and waste factor
        if not self.expected_flour_output:
            self.expected_flour_output = self.wheat_amount * ((100 - self.waste_factor) / 100)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Batch {self.batch_number} - {self.factory.name}"
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage based on actual vs expected output"""
        if self.expected_flour_output and self.expected_flour_output > 0:
            try:
                actual = Decimal(str(self.actual_flour_output))
                expected = Decimal(str(self.expected_flour_output))
                percent = (actual / expected) * Decimal('100')
                return float(min(percent, Decimal('100')))
            except Exception:
                return 0
        return 0
    
    @property
    def is_100_percent_complete(self):
        """Check if batch is 100% complete"""
        return self.progress_percentage >= 100
    
    @property
    def can_be_edited(self):
        """Check if batch can be edited (not stopped or completed)"""
        return self.status not in ['stopped', 'completed']
    
    @property
    def can_be_managed_by_super_admin(self):
        """Check if batch can be managed by super admin"""
        return self.status not in ['completed']
    
    @property
    def is_finalized(self):
        """Check if batch is in a final state (stopped or completed)"""
        return self.status in ['stopped', 'completed']
    
    def finalize_batch(self, user):
        """Finalize batch - set to stopped and lock all values"""
        if self.status not in ['in_process', 'paused']:
            raise ValueError("Only in-process or paused batches can be finalized")
        
        self.status = 'stopped'
        self.end_date = timezone.now()
        # Lock all values - no more changes allowed
        self.save(update_fields=['status', 'end_date'])
        
        # Create notification
        BatchNotification.objects.create(
            batch=self,
            notification_type='batch_stopped',
            message=f"Batch {self.batch_number} has been stopped and finalized by {user.username}"
        )
    
    def get_progress_color(self):
        """Get color based on progress percentage"""
        progress = self.progress_percentage
        if progress >= 100:
            return 'success'
        elif progress >= 75:
            return 'info'
        elif progress >= 50:
            return 'warning'
        else:
            return 'danger'

class BatchNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('batch_created', 'Batch Created'),
        ('batch_approved', 'Batch Approved'),
        ('batch_started', 'Batch Started'),
        ('batch_paused', 'Batch Paused'),
        ('batch_completed', 'Batch Completed'),
        ('batch_rejected', 'Batch Rejected'),
        ('batch_100_percent', 'Batch 100% Complete'),
    ]
    
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    sent_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='batch_notifications')
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.batch.batch_number}"

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
    
    # Notification types for different user roles
    NOTIFICATION_TYPES = [
        ('batch_assignment', 'Batch Assignment'),
        ('batch_approval', 'Batch Approval'),
        ('batch_rejection', 'Batch Rejection'),
        ('batch_completion', 'Batch Completion'),
        ('system_warning', 'System Warning'),
        ('device_alert', 'Device Alert'),
        ('production_alert', 'Production Alert'),
        ('maintenance_reminder', 'Maintenance Reminder'),
        ('user_management', 'User Management'),
        ('data_export', 'Data Export'),
        ('factory_status', 'Factory Status'),
    ]
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='system_warning')
    is_active = models.BooleanField(default=True)
    requires_admin = models.BooleanField(default=False)
    requires_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class UserNotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enabled_categories = models.ManyToManyField(NotificationCategory, blank=True)
    receive_in_app = models.BooleanField(default=True)
    receive_email = models.BooleanField(default=False)
    
    # Email settings
    email_address = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    
    # Permission settings
    can_modify_preferences = models.BooleanField(default=True)
    mandatory_notifications = models.ManyToManyField(NotificationCategory, blank=True, related_name='mandatory_users')
    
    # Role-based settings
    is_admin = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Auto-set email preferences if user has valid email
        if self.user.email and not self.email_address:
            self.email_address = self.user.email
            self.receive_email = True
        
        # Auto-set role-based settings
        if self.user.groups.filter(name='admin').exists():
            self.is_admin = True
        if self.user.groups.filter(name='Superadmin').exists() or self.user.is_superuser:
            self.is_super_admin = True
            
        super().save(*args, **kwargs)

class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default='Notification')
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Delivery channels
    sent_in_app = models.BooleanField(default=False)
    sent_email = models.BooleanField(default=False)
    
    # Email tracking
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_error = models.TextField(blank=True, null=True)
    
    # Related objects
    related_batch = models.ForeignKey('Batch', on_delete=models.CASCADE, null=True, blank=True)
    related_factory = models.ForeignKey('Factory', on_delete=models.CASCADE, null=True, blank=True)
    related_device = models.ForeignKey('Device', on_delete=models.CASCADE, null=True, blank=True)
    
    # User interaction
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    link = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category}: {self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save()

class EmailHistory(models.Model):
    """Track all emails sent to users with detailed information"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_history')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    email_type = models.CharField(max_length=50, choices=[
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
        ('notification', 'Notification'),
        ('custom', 'Custom Message'),
        ('mass_message', 'Mass Message'),
        ('system_alert', 'System Alert'),
    ])
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails_sent')
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ], default='pending')
    error_message = models.TextField(blank=True, null=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # For mass messages
    mass_message_group = models.CharField(max_length=50, blank=True, null=True)  # admin, user, super_admin, all
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name_plural = 'Email History'
    
    def __str__(self):
        return f"{self.email_type} to {self.user.username} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField()
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE, null=True, blank=True)
    template_type = models.CharField(max_length=50, choices=[
        ('notification', 'Notification'),
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
        ('custom', 'Custom Template'),
    ], default='notification')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Template variables
    variables = models.JSONField(default=dict, help_text="Available template variables")
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class MassMessage(models.Model):
    """For sending mass messages to user groups"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    subject = models.CharField(max_length=200)
    target_groups = models.JSONField(default=list, help_text="List of target groups: ['admin', 'user', 'super_admin', 'all']")
    target_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='mass_messages_received')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mass_messages_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], default='draft')
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.title} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

class Microsoft365Settings(models.Model):
    """Simple Microsoft 365 settings for OAuth2 authentication"""
    client_id = models.CharField(max_length=255, blank=True, help_text="Azure AD Application Client ID")
    client_secret = models.CharField(max_length=255, blank=True, help_text="Azure AD Application Client Secret")
    tenant_id = models.CharField(max_length=255, blank=True, help_text="Azure AD Tenant ID")
    auth_user = models.CharField(max_length=255, blank=True, help_text="User email for authentication (e.g., danny.v@...)")
    from_email = models.CharField(max_length=255, blank=True, help_text="Shared mailbox email (e.g., noreply@...)")
    from_name = models.CharField(max_length=255, default="Mill Application", help_text="From name for emails")
    
    # OAuth2 tokens
    access_token = models.TextField(blank=True, help_text="OAuth2 access token")
    refresh_token = models.TextField(blank=True, help_text="OAuth2 refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True, help_text="Token expiration time")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Active configuration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Microsoft 365 Settings"
        verbose_name_plural = "Microsoft 365 Settings"
    
    def __str__(self):
        return f"Microsoft 365 ({self.auth_user} -> {self.from_email})"
    
    def save(self, *args, **kwargs):
        # Ensure only one active configuration
        if self.is_active:
            Microsoft365Settings.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

class NotificationLog(models.Model):
    """Log for tracking notification delivery"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    delivery_method = models.CharField(max_length=20, choices=[('app', 'In-App'), ('email', 'Email')])
    status = models.CharField(max_length=20, choices=[('success', 'Success'), ('failed', 'Failed')])
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification} - {self.delivery_method} - {self.status}"

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['notification', 'delivery_method', 'status']),
        ]

class DoorOpenLogs(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='door_open_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    counter_id = models.IntegerField()  # Store the counter_4 value
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='door_logs_resolved'  # Changed this to avoid conflict
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Door Open Log'
        verbose_name_plural = 'Door Open Logs'

    def __str__(self):
        return f"Door Open Log - Device: {self.device.name} at {self.timestamp}"
        
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

    def get_responses(self):
        """Get all responses for this ticket"""
        return self.responses.all().order_by('created_at')

    def get_last_response(self):
        """Get the last response for this ticket"""
        return self.responses.last()

    def has_unread_responses(self, user):
        """Check if user has unread responses"""
        return self.responses.filter(
            created_by__isnull=False,
            created_by__is_staff=True,
            is_read=False
        ).exclude(created_by=user).exists()

    def mark_responses_as_read(self, user):
        """Mark all responses as read for a user"""
        self.responses.filter(
            created_by__isnull=False,
            created_by__is_staff=True,
            is_read=False
        ).exclude(created_by=user).update(is_read=True)


class TicketResponse(models.Model):
    """Responses to support tickets"""
    ticket = models.ForeignKey(ContactTicket, on_delete=models.CASCADE, related_name='responses')
    message = models.TextField()
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ticket_responses'
    )
    is_internal = models.BooleanField(default=False, help_text="Internal note not visible to user")
    is_read = models.BooleanField(default=False, help_text="Whether the response has been read")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Response'
        verbose_name_plural = 'Ticket Responses'

    def __str__(self):
        return f"Response to {self.ticket.subject} - {self.created_at}"

    def get_author_name(self):
        """Get the name of the response author"""
        if self.created_by:
            return self.created_by.get_full_name() or self.created_by.username
        return "System"

       
@receiver(pre_save, sender=RawData)
def handle_counter_4_change(sender, instance, **kwargs):
    try:
        # Get the previous state of this RawData instance
        old_instance = RawData.objects.get(id=instance.id)
        
        # Check if counter_4 has changed from null to a value
        if old_instance.counter_4 is None and instance.counter_4 is not None:
            # Create a new DoorOpenLogs entry
            DoorOpenLogs.objects.create(
                device=instance.device,
                counter_id=instance.counter_4
            )
    except RawData.DoesNotExist:
        # This is a new instance
        if instance.counter_4 is not None:
            # Create a new DoorOpenLogs entry for new instances with counter_4
            DoorOpenLogs.objects.create(
                device=instance.device,
                counter_id=instance.counter_4
            )
from django.db import models
from django.contrib.auth import get_user_model

class FeedbackCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Feedback Categories"

class Feedback(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    category = models.ForeignKey(FeedbackCategory, on_delete=models.CASCADE)
    factories = models.ManyToManyField('Factory', blank=True)
    all_factories = models.BooleanField(default=False)
    
    issue_date = models.DateField()
    expected_value = models.FloatField(null=True, blank=True)
    shown_value = models.FloatField(null=True, blank=True)
    
    subject = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.created_at.date()}"


class TVDashboardSettings(models.Model):
    """Settings for TV Dashboard display options"""
    
    DISPLAY_MODES = [
        ('all_factories', 'All Factories'),
        ('by_city', 'Group by City'),
        ('best_performing', 'Best Performing First'),
        ('worst_performing', 'Worst Performing First'),
        ('alphabetical', 'Alphabetical Order'),
        ('status_based', 'Status Based (Active/Inactive)'),
    ]
    
    SORT_CRITERIA = [
        ('daily_total', 'Daily Production'),
        ('weekly_total', 'Weekly Production'),
        ('monthly_total', 'Monthly Production'),
        ('yearly_total', 'Yearly Production'),
        ('name', 'Factory Name'),
        ('city', 'City Name'),
        ('status', 'Status'),
    ]
    
    REFRESH_INTERVALS = [
        (15, '15 seconds'),
        (30, '30 seconds'),
        (60, '1 minute'),
        (120, '2 minutes'),
        (300, '5 minutes'),
    ]
    
    AUTO_SCROLL_OPTIONS = [
        ('none', 'No Auto-scroll'),
        ('up', 'Scroll Up'),
        ('down', 'Scroll Down'),
        ('alternating', 'Alternating'),
    ]
    
    # Color Themes
    COLOR_THEMES = [
        ('default', 'Default Blue'),
        ('dark', 'Dark Theme'),
        ('light', 'Light Theme'),
        ('green', 'Green Theme'),
        ('purple', 'Purple Theme'),
        ('orange', 'Orange Theme'),
        ('red', 'Red Theme'),
        ('custom', 'Custom Colors'),
    ]
    
    # Font Families
    FONT_FAMILIES = [
        ('Arial', 'Arial'),
        ('Helvetica', 'Helvetica'),
        ('Times New Roman', 'Times New Roman'),
        ('Georgia', 'Georgia'),
        ('Verdana', 'Verdana'),
        ('Tahoma', 'Tahoma'),
        ('Trebuchet MS', 'Trebuchet MS'),
        ('Impact', 'Impact'),
        ('Comic Sans MS', 'Comic Sans MS'),
    ]
    
    # Background Styles
    BACKGROUND_STYLES = [
        ('gradient', 'Gradient Background'),
        ('solid', 'Solid Color'),
        ('pattern', 'Pattern Background'),
        ('image', 'Image Background'),
        ('animated', 'Animated Background'),
    ]
    
    # Animation Speeds
    ANIMATION_SPEEDS = [
        ('slow', 'Slow'),
        ('normal', 'Normal'),
        ('fast', 'Fast'),
        ('none', 'No Animation'),
    ]
    
    # Progress Bar Styles
    PROGRESS_STYLES = [
        ('linear', 'Linear Bar'),
        ('circular', 'Circular Progress'),
        ('steps', 'Step Indicator'),
        ('dots', 'Dot Progress'),
    ]
    
    # Basic Settings
    name = models.CharField(max_length=100, unique=True, help_text="Name for this TV dashboard configuration")
    is_active = models.BooleanField(default=True, help_text="Whether this configuration is currently active")
    
    # Display Settings
    display_mode = models.CharField(
        max_length=20, 
        choices=DISPLAY_MODES, 
        default='all_factories',
        help_text="How to organize factories on the display"
    )
    
    sort_criteria = models.CharField(
        max_length=20,
        choices=SORT_CRITERIA,
        default='daily_total',
        help_text="Primary sorting criteria for factories"
    )
    
    sort_direction = models.CharField(
        max_length=4,
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        default='desc',
        help_text="Sort direction"
    )
    
    # Filter Settings
    selected_cities = models.ManyToManyField(
        City, 
        blank=True,
        help_text="Cities to include in the display (empty = all cities)"
    )
    
    selected_factories = models.ManyToManyField(
        Factory,
        blank=True,
        help_text="Specific factories to include (empty = all factories)"
    )
    
    show_only_active = models.BooleanField(
        default=False,
        help_text="Show only active factories"
    )
    
    # Visual Settings
    show_summary_stats = models.BooleanField(
        default=True,
        help_text="Show summary statistics at the top"
    )
    
    show_factory_status = models.BooleanField(
        default=True,
        help_text="Show factory status indicators"
    )
    
    show_time_info = models.BooleanField(
        default=True,
        help_text="Show start/stop time information"
    )
    
    # Additional Visual Toggle Settings
    show_production_charts = models.BooleanField(
        default=True,
        help_text="Show production charts and graphs"
    )
    
    show_performance_metrics = models.BooleanField(
        default=True,
        help_text="Show performance metrics and KPIs"
    )
    
    show_alert_notifications = models.BooleanField(
        default=True,
        help_text="Show alert notifications and warnings"
    )
    
    show_system_status = models.BooleanField(
        default=True,
        help_text="Show system status and health indicators"
    )
    
    show_weather_info = models.BooleanField(
        default=False,
        help_text="Show weather information (if available)"
    )
    
    show_clock_display = models.BooleanField(
        default=True,
        help_text="Show current time and date display"
    )
    
    show_production_targets = models.BooleanField(
        default=True,
        help_text="Show production targets and goals"
    )
    
    show_efficiency_ratios = models.BooleanField(
        default=True,
        help_text="Show efficiency ratios and percentages"
    )
    
    show_quality_metrics = models.BooleanField(
        default=True,
        help_text="Show quality metrics and standards"
    )
    
    show_maintenance_status = models.BooleanField(
        default=True,
        help_text="Show maintenance status and schedules"
    )
    
    show_energy_consumption = models.BooleanField(
        default=False,
        help_text="Show energy consumption data"
    )
    
    show_temperature_readings = models.BooleanField(
        default=False,
        help_text="Show temperature readings from sensors"
    )
    
    show_humidity_levels = models.BooleanField(
        default=False,
        help_text="Show humidity levels from sensors"
    )
    
    show_pressure_readings = models.BooleanField(
        default=False,
        help_text="Show pressure readings from sensors"
    )
    
    show_vibration_data = models.BooleanField(
        default=False,
        help_text="Show vibration data from sensors"
    )
    
    show_door_status = models.BooleanField(
        default=True,
        help_text="Show door open/close status"
    )
    
    show_power_consumption = models.BooleanField(
        default=False,
        help_text="Show power consumption data"
    )
    
    show_network_status = models.BooleanField(
        default=True,
        help_text="Show network connectivity status"
    )
    
    show_device_health = models.BooleanField(
        default=True,
        help_text="Show device health and status"
    )
    
    show_batch_information = models.BooleanField(
        default=True,
        help_text="Show current batch information"
    )
    
    show_shift_information = models.BooleanField(
        default=False,
        help_text="Show shift information and schedules"
    )
    
    show_operator_info = models.BooleanField(
        default=False,
        help_text="Show current operator information"
    )
    
    show_safety_alerts = models.BooleanField(
        default=True,
        help_text="Show safety alerts and warnings"
    )
    
    show_maintenance_alerts = models.BooleanField(
        default=True,
        help_text="Show maintenance alerts and reminders"
    )
    
    show_quality_alerts = models.BooleanField(
        default=True,
        help_text="Show quality control alerts"
    )
    
    show_production_alerts = models.BooleanField(
        default=True,
        help_text="Show production-related alerts"
    )
    
    show_system_alerts = models.BooleanField(
        default=True,
        help_text="Show system and technical alerts"
    )
    
    # Color Theme Settings
    color_theme = models.CharField(
        max_length=20,
        choices=COLOR_THEMES,
        default='default',
        help_text="Color theme for the dashboard"
    )
    
    primary_color = models.CharField(
        max_length=7,
        default='#0d6efd',
        help_text="Primary color (hex code)"
    )
    
    secondary_color = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text="Secondary color (hex code)"
    )
    
    accent_color = models.CharField(
        max_length=7,
        default='#FFD700',
        help_text="Accent color (hex code)"
    )
    
    success_color = models.CharField(
        max_length=7,
        default='#198754',
        help_text="Success color (hex code)"
    )
    
    warning_color = models.CharField(
        max_length=7,
        default='#ffc107',
        help_text="Warning color (hex code)"
    )
    
    danger_color = models.CharField(
        max_length=7,
        default='#dc3545',
        help_text="Danger color (hex code)"
    )
    
    # Font Settings
    font_family = models.CharField(
        max_length=50,
        choices=FONT_FAMILIES,
        default='Arial',
        help_text="Font family for text"
    )
    
    font_size_base = models.IntegerField(
        default=16,
        validators=[MinValueValidator(12), MaxValueValidator(24)],
        help_text="Base font size in pixels"
    )
    
    font_size_large = models.IntegerField(
        default=20,
        validators=[MinValueValidator(16), MaxValueValidator(32)],
        help_text="Large font size in pixels"
    )
    
    font_size_xlarge = models.IntegerField(
        default=24,
        validators=[MinValueValidator(20), MaxValueValidator(48)],
        help_text="Extra large font size in pixels"
    )
    
    font_weight = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'Normal'),
            ('bold', 'Bold'),
            ('lighter', 'Lighter'),
            ('bolder', 'Bolder'),
        ],
        default='normal',
        help_text="Font weight"
    )
    
    # Background Settings
    background_style = models.CharField(
        max_length=20,
        choices=BACKGROUND_STYLES,
        default='gradient',
        help_text="Background style"
    )
    
    background_color = models.CharField(
        max_length=7,
        default='#1e3c72',
        help_text="Background color (hex code)"
    )
    
    background_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL for background image"
    )
    
    # Card Styling
    card_border_radius = models.IntegerField(
        default=15,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Card border radius in pixels"
    )
    
    card_shadow = models.CharField(
        max_length=20,
        choices=[
            ('none', 'No Shadow'),
            ('light', 'Light Shadow'),
            ('medium', 'Medium Shadow'),
            ('heavy', 'Heavy Shadow'),
        ],
        default='medium',
        help_text="Card shadow style"
    )
    
    card_transparency = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Card transparency percentage"
    )
    
    card_border_width = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Card border width in pixels"
    )
    
    # Animation Settings
    animation_speed = models.CharField(
        max_length=10,
        choices=ANIMATION_SPEEDS,
        default='normal',
        help_text="Animation speed"
    )
    
    hover_effects = models.BooleanField(
        default=True,
        help_text="Enable hover effects on cards"
    )
    
    transition_effects = models.BooleanField(
        default=True,
        help_text="Enable transition effects"
    )
    
    # Layout Settings
    cards_per_row = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        help_text="Number of factory cards per row"
    )
    
    show_city_headers = models.BooleanField(
        default=True,
        help_text="Show city headers when grouping by city"
    )
    
    card_spacing = models.IntegerField(
        default=25,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Spacing between cards in pixels"
    )
    
    section_padding = models.IntegerField(
        default=20,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Padding around sections in pixels"
    )
    
    # Progress Indicators
    show_progress_bars = models.BooleanField(
        default=True,
        help_text="Show progress bars for production data"
    )
    
    progress_style = models.CharField(
        max_length=20,
        choices=PROGRESS_STYLES,
        default='linear',
        help_text="Style of progress indicators"
    )
    
    progress_animation = models.BooleanField(
        default=True,
        help_text="Animate progress bars"
    )
    
    # Alert Styling
    show_alerts = models.BooleanField(
        default=True,
        help_text="Show alert notifications"
    )
    
    alert_position = models.CharField(
        max_length=20,
        choices=[
            ('top-right', 'Top Right'),
            ('top-left', 'Top Left'),
            ('bottom-right', 'Bottom Right'),
            ('bottom-left', 'Bottom Left'),
            ('center', 'Center'),
        ],
        default='top-right',
        help_text="Position of alert notifications"
    )
    
    alert_duration = models.IntegerField(
        default=5000,
        validators=[MinValueValidator(1000), MaxValueValidator(30000)],
        help_text="Alert display duration in milliseconds"
    )
    
    # Auto-refresh and Animation
    refresh_interval = models.IntegerField(
        choices=REFRESH_INTERVALS,
        default=30,
        help_text="How often to refresh the dashboard data"
    )
    
    auto_scroll = models.CharField(
        max_length=15,
        choices=AUTO_SCROLL_OPTIONS,
        default='none',
        help_text="Auto-scroll behavior"
    )
    
    scroll_speed = models.IntegerField(
        default=120,
        help_text="Scroll speed in seconds (for full cycle)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tv_settings'
    )
    
    class Meta:
        verbose_name = 'TV Dashboard Setting'
        verbose_name_plural = 'TV Dashboard Settings'
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_display_mode_display()})"
    
    def get_factories_queryset(self):
        """Get filtered and sorted factories based on settings"""
        from django.db.models import Q
        
        # Start with all factories
        factories = Factory.objects.all()
        
        # Apply city filter
        if self.selected_cities.exists():
            factories = factories.filter(city__in=self.selected_cities.all())
        
        # Apply factory filter
        if self.selected_factories.exists():
            factories = factories.filter(id__in=self.selected_factories.all())
        
        # Apply status filter
        if self.show_only_active:
            factories = factories.filter(status=True)
        
        # Apply sorting
        if self.sort_criteria == 'city':
            if self.sort_direction == 'desc':
                factories = factories.order_by('-city__name')
            else:
                factories = factories.order_by('city__name')
        elif self.sort_criteria in ['daily_total', 'weekly_total', 'monthly_total', 'yearly_total']:
            # These will be sorted in the view after calculating totals
            factories = factories.order_by('name')
        else:
            order_field = self.sort_criteria
            if self.sort_direction == 'desc':
                order_field = f'-{order_field}'
            factories = factories.order_by(order_field)
        
        return factories
    
    def get_display_url(self):
        """Get the URL for this TV dashboard configuration"""
        from django.urls import reverse
        return f"{reverse('tv-dashboard')}?config={self.id}"
    
    @classmethod
    def get_active_config(cls):
        """Get the currently active TV dashboard configuration"""
        return cls.objects.filter(is_active=True).first()
    
    def get_css_variables(self):
        """Get CSS variables for the current theme"""
        variables = {
            '--primary-color': self.primary_color,
            '--secondary-color': self.secondary_color,
            '--accent-color': self.accent_color,
            '--success-color': self.success_color,
            '--warning-color': self.warning_color,
            '--danger-color': self.danger_color,
            '--font-family': self.font_family,
            '--font-size-base': f'{self.font_size_base}px',
            '--font-size-large': f'{self.font_size_large}px',
            '--font-size-xlarge': f'{self.font_size_xlarge}px',
            '--font-weight': self.font_weight,
            '--card-border-radius': f'{self.card_border_radius}px',
            '--card-transparency': f'{self.card_transparency / 100}',
            '--card-border-width': f'{self.card_border_width}px',
            '--card-spacing': f'{self.card_spacing}px',
            '--section-padding': f'{self.section_padding}px',
        }
        
        # Add shadow styles
        if self.card_shadow == 'light':
            variables['--card-shadow'] = '0 2px 4px rgba(0,0,0,0.1)'
        elif self.card_shadow == 'medium':
            variables['--card-shadow'] = '0 4px 8px rgba(0,0,0,0.15)'
        elif self.card_shadow == 'heavy':
            variables['--card-shadow'] = '0 8px 16px rgba(0,0,0,0.2)'
        else:
            variables['--card-shadow'] = 'none'
        
        # Add animation duration
        if self.animation_speed == 'slow':
            variables['--animation-duration'] = '0.5s'
        elif self.animation_speed == 'fast':
            variables['--animation-duration'] = '0.15s'
        elif self.animation_speed == 'none':
            variables['--animation-duration'] = '0s'
        else:
            variables['--animation-duration'] = '0.3s'
        
        return variables

class TwoFactorAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=32, unique=True)
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"2FA for {self.user.username}"
    
    class Meta:
        verbose_name = "Two Factor Authentication"
        verbose_name_plural = "Two Factor Authentications"

class PowerEvent(models.Model):
    """Track power events for devices"""
    EVENT_TYPES = [
        ('power_loss', 'Power Loss'),
        ('power_restored', 'Power Restored'),
        ('production_without_power', 'Production Without Power'),
        ('power_fluctuation', 'Power Fluctuation'),
        ('battery_low', 'Battery Low'),
        ('power_surge', 'Power Surge'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='power_events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    
    # Power data
    ain1_value = models.FloatField(null=True, blank=True, help_text="Power value when event occurred")
    previous_ain1_value = models.FloatField(null=True, blank=True, help_text="Previous power value")
    
    # Production data at time of event
    counter_1_value = models.IntegerField(null=True, blank=True)
    counter_2_value = models.IntegerField(null=True, blank=True)
    counter_3_value = models.IntegerField(null=True, blank=True)
    counter_4_value = models.IntegerField(null=True, blank=True)
    
    # Event details
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_power_events'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    # Notification tracking
    notification_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    super_admin_notified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['device', 'event_type', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.get_event_type_display()} ({self.created_at})"
    
    def get_severity_color(self):
        """Return Bootstrap color class based on severity"""
        colors = {
            'low': 'info',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        return colors.get(self.severity, 'secondary')
    
    def mark_as_resolved(self, user, notes=""):
        """Mark power event as resolved"""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()

class DevicePowerStatus(models.Model):
    """Current power status for each device"""
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='power_status')
    
    # Current power state
    has_power = models.BooleanField(default=True)
    ain1_value = models.FloatField(null=True, blank=True)
    last_power_check = models.DateTimeField(auto_now=True)
    
    # Power thresholds
    power_threshold = models.FloatField(default=0.0, help_text="Minimum power value to consider device as powered")
    
    # Status tracking
    power_loss_detected_at = models.DateTimeField(null=True, blank=True)
    power_restored_at = models.DateTimeField(null=True, blank=True)
    
    # Production tracking during power loss
    production_during_power_loss = models.BooleanField(default=False)
    last_production_check = models.DateTimeField(null=True, blank=True)
    
    # Notification settings
    notify_on_power_loss = models.BooleanField(default=True)
    notify_on_power_restore = models.BooleanField(default=True)
    notify_on_production_without_power = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Device Power Status'
        verbose_name_plural = 'Device Power Statuses'
        indexes = [
            models.Index(fields=['has_power', 'updated_at']),
            models.Index(fields=['device', 'has_power']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - Power: {'ON' if self.has_power else 'OFF'}"
    
    def update_power_status(self, ain1_value):
        """Update power status based on ain1_value"""
        previous_has_power = self.has_power
        self.ain1_value = ain1_value
        self.last_power_check = timezone.now()
        
        # Determine if device has power
        self.has_power = ain1_value > self.power_threshold
        
        # Handle power loss
        if not self.has_power and previous_has_power:
            self.power_loss_detected_at = timezone.now()
            self.power_restored_at = None
            
        # Handle power restoration
        elif self.has_power and not previous_has_power:
            self.power_restored_at = timezone.now()
            
        self.save()
        return previous_has_power != self.has_power  # Return True if status changed
    
    def check_production_without_power(self, counter_values):
        """Check if production is happening without power"""
        if not self.has_power:
            # Get the last production data
            last_production = ProductionData.objects.filter(device=self.device).order_by('-created_at').first()
            
            if last_production:
                # Check if any counter has increased
                for counter_name, current_value in counter_values.items():
                    if counter_name == 'counter_1' and current_value > last_production.daily_production:
                        self.production_during_power_loss = True
                        self.last_production_check = timezone.now()
                        self.save()
                        return True
                        
        return False
    
    def get_status_display(self):
        """Get human-readable status"""
        if self.has_power:
            return "Power ON"
        else:
            return "Power OFF"
    
    def get_status_color(self):
        """Get Bootstrap color for status"""
        if self.has_power:
            return "success"
        else:
            return "danger"

class PowerNotificationSettings(models.Model):
    """Settings for power-related notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='power_notification_settings')
    
    # Notification preferences
    notify_power_loss = models.BooleanField(default=True)
    notify_power_restore = models.BooleanField(default=True)
    notify_production_without_power = models.BooleanField(default=True)
    notify_power_fluctuation = models.BooleanField(default=False)
    
    # Email preferences
    email_power_loss = models.BooleanField(default=True)
    email_power_restore = models.BooleanField(default=False)
    email_production_without_power = models.BooleanField(default=True)
    email_power_fluctuation = models.BooleanField(default=False)
    
    # Device assignments
    responsible_devices = models.ManyToManyField(Device, blank=True, related_name='power_responsible_users')
    
    # Notification frequency
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
        ],
        default='immediate'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Power Notification Setting'
        verbose_name_plural = 'Power Notification Settings'
    
    def __str__(self):
        return f"Power notifications for {self.user.username}"


class PowerManagementPermission(models.Model):
    """Model to track which users have access to power management features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='power_management_permission')
    can_access_power_management = models.BooleanField(default=False)
    can_view_power_status = models.BooleanField(default=False)
    can_resolve_power_events = models.BooleanField(default=False)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='power_permissions_granted')
    granted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Power Management Permission"
        verbose_name_plural = "Power Management Permissions"

    def __str__(self):
        return f"Power Management Permission for {self.user.username}"

    @classmethod
    def has_power_access(cls, user):
        """Check if user has power management access"""
        if user.is_superuser:
            return True
        try:
            permission = cls.objects.get(user=user)
            return permission.can_access_power_management
        except cls.DoesNotExist:
            return False

    @classmethod
    def has_power_status_access(cls, user):
        """Check if user has power status viewing access"""
        if user.is_superuser:
            return True
        try:
            permission = cls.objects.get(user=user)
            return permission.can_view_power_status
        except cls.DoesNotExist:
            return False
