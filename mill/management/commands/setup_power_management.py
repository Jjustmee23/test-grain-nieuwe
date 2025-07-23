from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from mill.models import Device, DevicePowerStatus, PowerManagementPermission, PowerNotificationSettings
from django.utils import timezone

class Command(BaseCommand):
    help = 'Setup power management permissions and initial power status for devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grant-super-admin-permissions',
            action='store_true',
            help='Grant power management permissions to all super admins',
        )
        parser.add_argument(
            '--create-power-status',
            action='store_true',
            help='Create power status records for all devices',
        )
        parser.add_argument(
            '--setup-notifications',
            action='store_true',
            help='Setup power notification settings for super admins',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting power management setup...'))

        if options['grant_super_admin_permissions']:
            self.grant_super_admin_permissions()

        if options['create_power_status']:
            self.create_power_status()

        if options['setup_notifications']:
            self.setup_notifications()

        if not any([options['grant_super_admin_permissions'], options['create_power_status'], options['setup_notifications']]):
            # Run all if no specific option is provided
            self.grant_super_admin_permissions()
            self.create_power_status()
            self.setup_notifications()

        self.stdout.write(self.style.SUCCESS('Power management setup completed!'))

    def grant_super_admin_permissions(self):
        """Grant power management permissions to all super admins"""
        self.stdout.write('Granting power management permissions to super admins...')
        
        super_admins = User.objects.filter(is_superuser=True)
        granted_count = 0
        
        for user in super_admins:
            permission, created = PowerManagementPermission.objects.get_or_create(
                user=user,
                defaults={
                    'can_access_power_management': True,
                    'can_view_power_status': True,
                    'can_resolve_power_events': True,
                    'granted_by': user,
                    'notes': 'Auto-granted during setup'
                }
            )
            
            if created:
                granted_count += 1
                self.stdout.write(f'  ✓ Granted permissions to {user.username}')
            else:
                # Update existing permissions
                permission.can_access_power_management = True
                permission.can_view_power_status = True
                permission.can_resolve_power_events = True
                permission.save()
                self.stdout.write(f'  ✓ Updated permissions for {user.username}')
        
        self.stdout.write(self.style.SUCCESS(f'Granted permissions to {granted_count} super admins'))

    def create_power_status(self):
        """Create power status records for all devices"""
        self.stdout.write('Creating power status records for devices...')
        
        # Only get devices that belong to factories
        devices = Device.objects.filter(factory__isnull=False)
        created_count = 0
        
        for device in devices:
            power_status, created = DevicePowerStatus.objects.get_or_create(
                device=device,
                defaults={
                    'has_power': True,  # Assume devices have power initially
                    'power_threshold': 0.0,
                    'notify_on_power_loss': True,
                    'notify_on_power_restore': True,
                    'notify_on_production_without_power': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created power status for {device.name} ({device.factory.name})')
        
        self.stdout.write(self.style.SUCCESS(f'Created power status for {created_count} devices'))

    def setup_notifications(self):
        """Setup power notification settings for super admins"""
        self.stdout.write('Setting up power notification settings for super admins...')
        
        super_admins = User.objects.filter(is_superuser=True)
        setup_count = 0
        
        for user in super_admins:
            settings, created = PowerNotificationSettings.objects.get_or_create(
                user=user,
                defaults={
                    'notify_power_loss': True,
                    'notify_power_restore': True,
                    'notify_production_without_power': True,
                    'notify_power_fluctuation': False,
                    'email_power_loss': True,
                    'email_power_restore': False,
                    'email_production_without_power': True,
                    'email_power_fluctuation': False,
                    'notification_frequency': 'immediate',
                }
            )
            
            if created:
                setup_count += 1
                self.stdout.write(f'  ✓ Setup notifications for {user.username}')
            else:
                self.stdout.write(f'  ✓ Notifications already setup for {user.username}')
        
        self.stdout.write(self.style.SUCCESS(f'Setup notifications for {setup_count} super admins')) 