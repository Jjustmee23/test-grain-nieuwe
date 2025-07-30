from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from mill.models import NotificationCategory, UserProfile , UserNotificationPreference, Batch , Notification, Factory, Device, BatchNotification
from django.contrib.auth.models import Group , User
from django.utils import timezone
from django.core.mail import send_mail
import sys

def is_running_update_batches():
    return any('update_batches' in arg for arg in sys.argv)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        UserNotificationPreference.objects.create(user=instance)

@receiver(post_save, sender=Batch)
def notify_admins_on_batch_creation(sender, instance, created, **kwargs):
    if created:
        try:
            admin_group = Group.objects.get(name='Admin')  
        except:
            pass  
        users = User.objects.all()
    # TODO:
        #get user with group admin
        # filter these users that user.Userprofile.allowed_factories contains instance.factory
        # 
        for user in users:
            Notification.objects.create(
                user=user,
                category=NotificationCategory.objects.get(name='Batch'),
                message=f"New batch is created with batch id '{instance.id}' for factory '{instance.factory.name}'",
                link=f"/batches/"  
            )

@receiver(post_save, sender=Batch)
def notify_admins_on_batch_acceptance(sender, instance, created, **kwargs):
    if not created:  # This ensures the signal is triggered for updates only
        if is_running_update_batches():
            return
        try:
            users = User.objects.filter(groups__name__in=['Admin', 'Superadmin'])
            notification_category = NotificationCategory.objects.get(name='Batch')
            for user in users:
                Notification.objects.create(
                    user=user,
                    category=notification_category,
                    message=f"Batch status for batch id '{instance.id}' is updated for factory '{instance.factory.name}'",
                    link=f"/batches/"
                )
        except NotificationCategory.DoesNotExist:
            # Handle the case where the NotificationCategory does not exist
            pass

@receiver(post_save, sender=Factory)
def notify_admins_on_factory_update(sender, instance, created, **kwargs):
    if not created:  # This ensures the signal is triggered for updates only
        try:
            users = User.objects.filter(groups__name__in=['Admin', 'Superadmin'])
            notification_category = NotificationCategory.objects.get(name='Factory')
            for user in users:
                Notification.objects.create(
                    user=user,
                    category=notification_category,
                    message=f"Factory statis with id '{instance.id}' is updated",
                    link=f"/manage-factory/"
                )
        except NotificationCategory.DoesNotExist:
            # Handle the case where the NotificationCategory does not exist
            pass

@receiver(post_save, sender=Device)
def notify_admins_on_device_updates(sender, instance, created, **kwargs):
    if not created:
        print(' if not created')
        try:
            users = User.objects.filter(groups__name__in=['Admin', 'Superadmin'])
            notification_category = NotificationCategory.objects.get(name='Device')
            for user in users:
                Notification.objects.create(
                    user=user,
                    category=notification_category,
                    message=f"Device statis with id '{instance.id}' is updated",
                    link=f"/manage-devices/"
                )
        except NotificationCategory.DoesNotExist:
            # Handle the case where the NotificationCategory does not exist
            pass

# New Batch Notification Signals
@receiver(post_save, sender=Batch)
def notify_factory_admins_on_batch_creation(sender, instance, created, **kwargs):
    """Notify factory admins when a new batch is created"""
    if created:
        # Get all admins who have access to this factory
        factory_admins = User.objects.filter(
            groups__name__in=['Admin', 'Superadmin'],
            userprofile__allowed_factories=instance.factory
        ).distinct()
        
        # Create batch notification
        notification = BatchNotification.objects.create(
            batch=instance,
            notification_type='batch_created',
            message=f"New batch {instance.batch_number} has been created for {instance.factory.name}. Please review and approve."
        )
        notification.sent_to.set(factory_admins)
        
        # Send in-app notifications
        for user in factory_admins:
            Notification.objects.create(
                user=user,
                category=NotificationCategory.objects.get_or_create(name='Batch')[0],
                message=f"New batch {instance.batch_number} created for {instance.factory.name}",
                link=f"/batches/{instance.id}/"
            )
        
        # Send email notifications
        for user in factory_admins:
            if hasattr(user, 'usernotificationpreference') and user.usernotificationpreference.receive_email:
                try:
                    send_mail(
                        subject=f"New Batch Created - {instance.batch_number}",
                        message=f"A new batch {instance.batch_number} has been created for {instance.factory.name}. Please log in to review and approve.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True
                    )
                    notification.email_sent = True
                    notification.save()
                except Exception as e:
                    print(f"Failed to send email to {user.email}: {e}")

@receiver(post_save, sender=Batch)
def notify_on_batch_status_change(sender, instance, **kwargs):
    """Notify when batch status changes"""
    if not kwargs.get('created'):  # Only for updates
        if is_running_update_batches():
            return
        try:
            old_instance = Batch.objects.get(pk=instance.pk)
        except Batch.DoesNotExist:
            return
        
        # Check if status changed
        if old_instance.status != instance.status:
            factory_admins = User.objects.filter(
                groups__name__in=['Admin', 'Superadmin'],
                userprofile__allowed_factories=instance.factory
            ).distinct()
            
            notification_type_map = {
                'approved': 'batch_approved',
                'in_process': 'batch_started',
                'paused': 'batch_paused',
                'stopped': 'batch_stopped',
                'completed': 'batch_completed',
                'rejected': 'batch_rejected'
            }
            
            if instance.status in notification_type_map:
                notification = BatchNotification.objects.create(
                    batch=instance,
                    notification_type=notification_type_map[instance.status],
                    message=f"Batch {instance.batch_number} status changed to {instance.get_status_display()}"
                )
                notification.sent_to.set(factory_admins)
                
                # Send in-app notifications
                for user in factory_admins:
                    Notification.objects.create(
                        user=user,
                        category=NotificationCategory.objects.get_or_create(name='Batch')[0],
                        message=f"Batch {instance.batch_number} status: {instance.get_status_display()}",
                        link=f"/batches/{instance.id}/"
                    )

@receiver(post_save, sender=Batch)
def notify_on_batch_completion(sender, instance, **kwargs):
    """Notify when batch reaches 100% completion"""
    if is_running_update_batches():
        return
        
    if not kwargs.get('created') and instance.is_100_percent_complete:
        factory_admins = User.objects.filter(
            groups__name__in=['Admin', 'Superadmin'],
            userprofile__allowed_factories=instance.factory
        ).distinct()
        
        notification = BatchNotification.objects.create(
            batch=instance,
            notification_type='batch_100_percent',
            message=f"Batch {instance.batch_number} has reached 100% completion!"
        )
        notification.sent_to.set(factory_admins)
        
        # Send in-app notifications
        for user in factory_admins:
            Notification.objects.create(
                user=user,
                category=NotificationCategory.objects.get_or_create(name='Batch')[0],
                message=f"🎉 Batch {instance.batch_number} is 100% complete!",
                link=f"/batches/{instance.id}/"
            )
        
        # Auto-complete the batch (prevent recursion)
        Batch.objects.filter(pk=instance.pk).update(
            status='completed',
            is_completed=True,
            end_date=timezone.now()
        )
