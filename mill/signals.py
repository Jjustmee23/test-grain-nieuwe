from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from mill.models import NotificationCategory, UserProfile , UserNotificationPreference, Batch , Notification, Factory, Device
from django.contrib.auth.models import Group , User

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
        try:
            users = User.objects.filter(groups__name__in=['Admin', 'SuperAdmin'])
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
            users = User.objects.filter(groups__name__in=['Admin', 'SuperAdmin'])
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
            users = User.objects.filter(groups__name__in=['Admin', 'SuperAdmin'])
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
