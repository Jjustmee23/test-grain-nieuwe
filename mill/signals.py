from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from mill.models import NotificationCategory, UserProfile , UserNotificationPreference, Batch , Notification
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
                message=f"New batch is created with batch id {instance.id} for factory {instance.factory.name}",
                link=f"/batches/"  
            )