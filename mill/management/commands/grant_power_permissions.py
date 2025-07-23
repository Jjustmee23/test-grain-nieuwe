from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mill.models import PowerManagementPermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Grant power management permissions to specific users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to grant permissions to'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email to grant permissions to'
        )
        parser.add_argument(
            '--permissions',
            type=str,
            choices=['view', 'manage', 'resolve', 'all'],
            default='view',
            help='Type of permissions to grant'
        )
        parser.add_argument(
            '--granted-by',
            type=str,
            help='Username of the user granting the permissions'
        )
        parser.add_argument(
            '--notes',
            type=str,
            default='',
            help='Notes about the permission grant'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all users with power management permissions'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_permissions()
            return

        username = options['username']
        email = options['email']
        permissions = options['permissions']
        granted_by_username = options['granted_by']
        notes = options['notes']

        if not username and not email:
            self.stdout.write(
                self.style.ERROR('Please provide either --username or --email')
            )
            return

        # Find the user
        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User not found: {username or email}')
            )
            return

        # Find the granting user
        granted_by = None
        if granted_by_username:
            try:
                granted_by = User.objects.get(username=granted_by_username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Granting user not found: {granted_by_username}')
                )

        # Set permissions based on type
        can_view = permissions in ['view', 'manage', 'resolve', 'all']
        can_manage = permissions in ['manage', 'resolve', 'all']
        can_resolve = permissions in ['resolve', 'all']

        # Create or update permission
        permission, created = PowerManagementPermission.objects.get_or_create(
            user=user,
            defaults={
                'can_access_power_management': can_manage,
                'can_view_power_status': can_view,
                'can_resolve_power_events': can_resolve,
                'granted_by': granted_by,
                'notes': notes
            }
        )

        if not created:
            permission.can_access_power_management = can_manage
            permission.can_view_power_status = can_view
            permission.can_resolve_power_events = can_resolve
            if granted_by:
                permission.granted_by = granted_by
            if notes:
                permission.notes = notes
            permission.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully granted {permissions} permissions to {user.username} ({user.email})'
            )
        )

    def list_permissions(self):
        """List all users with power management permissions"""
        permissions = PowerManagementPermission.objects.select_related('user', 'granted_by').all()
        
        if not permissions:
            self.stdout.write('No power management permissions found.')
            return

        self.stdout.write('\nPower Management Permissions:')
        self.stdout.write('=' * 80)
        
        for perm in permissions:
            self.stdout.write(f'User: {perm.user.username} ({perm.user.email})')
            self.stdout.write(f'  - View Power Status: {perm.can_view_power_status}')
            self.stdout.write(f'  - Access Power Management: {perm.can_access_power_management}')
            self.stdout.write(f'  - Resolve Power Events: {perm.can_resolve_power_events}')
            self.stdout.write(f'  - Granted by: {perm.granted_by.username if perm.granted_by else "System"}')
            self.stdout.write(f'  - Granted at: {perm.granted_at}')
            if perm.notes:
                self.stdout.write(f'  - Notes: {perm.notes}')
            self.stdout.write('-' * 40) 