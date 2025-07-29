from django.core.management.base import BaseCommand
from mill.models import NotificationCategory

class Command(BaseCommand):
    help = 'Setup support tickets notification category'

    def handle(self, *args, **options):
        # Create support_tickets notification category
        category, created = NotificationCategory.objects.get_or_create(
            name='support_tickets',
            defaults={
                'description': 'Notifications related to support tickets',
                'notification_type': 'user_management',
                'is_active': True,
                'requires_admin': False,
                'requires_super_admin': False
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created notification category: {category.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Notification category already exists: {category.name}')
            ) 