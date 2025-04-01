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
        admin_group = Group.objects.get(name='Admin')  # Change to your group name
        users = User.objects.all()

        for user in users:
            Notification.objects.create(
                user=user,
                category=NotificationCategory.objects.get(name='Batch'),
                message=f"New batch created",
                link=f"/batches/"  
            )