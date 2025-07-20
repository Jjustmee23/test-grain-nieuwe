from django.core.management.base import BaseCommand
from mill.models import Microsoft365Settings


class Command(BaseCommand):
    help = 'Update the auth_user setting to noreply@nexonsolutions.be'

    def handle(self, *args, **options):
        try:
            # Get the active Microsoft 365 settings
            settings = Microsoft365Settings.objects.filter(is_active=True).first()
            
            if not settings:
                self.stdout.write(
                    self.style.WARNING('No active Microsoft 365 settings found. Creating new settings...')
                )
                settings = Microsoft365Settings.objects.create(
                    is_active=True,
                    auth_user='noreply@nexonsolutions.be',
                    from_email='noreply@nexonsolutions.be',
                    from_name='Mill Application'
                )
                self.stdout.write(
                    self.style.SUCCESS('Created new Microsoft 365 settings with noreply@nexonsolutions.be')
                )
            else:
                # Update existing settings
                old_auth_user = settings.auth_user
                settings.auth_user = 'noreply@nexonsolutions.be'
                settings.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Updated auth_user from {old_auth_user} to noreply@nexonsolutions.be')
                )
            
            # Display current settings
            self.stdout.write('')
            self.stdout.write('Current Microsoft 365 Settings:')
            self.stdout.write(f'  Auth User: {settings.auth_user}')
            self.stdout.write(f'  From Email: {settings.from_email}')
            self.stdout.write(f'  From Name: {settings.from_name}')
            self.stdout.write(f'  Is Active: {settings.is_active}')
            self.stdout.write(f'  Has Refresh Token: {bool(settings.refresh_token)}')
            
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('IMPORTANT: After updating auth_user, you may need to:'))
            self.stdout.write('1. Re-authorize OAuth2 for the new email address')
            self.stdout.write('2. Grant "Send As" permissions for noreply@nexonsolutions.be')
            self.stdout.write('3. Test email sending to ensure it works correctly')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating auth_user: {e}')
            ) 