from django.core.management.base import BaseCommand
from mill.models import Microsoft365Settings


class Command(BaseCommand):
    help = 'Update the from_email setting to noreply@nexonsolutions.be'

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
                    from_email='noreply@nexonsolutions.be',
                    from_name='Mill Application'
                )
                self.stdout.write(
                    self.style.SUCCESS('Created new Microsoft 365 settings with noreply@nexonsolutions.be')
                )
            else:
                # Update existing settings
                old_email = settings.from_email
                settings.from_email = 'noreply@nexonsolutions.be'
                settings.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Updated from_email from {old_email} to noreply@nexonsolutions.be')
                )
            
            # Display current settings
            self.stdout.write('')
            self.stdout.write('Current Microsoft 365 Settings:')
            self.stdout.write(f'  From Email: {settings.from_email}')
            self.stdout.write(f'  From Name: {settings.from_name}')
            self.stdout.write(f'  Auth User: {settings.auth_user or "Not set"}')
            self.stdout.write(f'  Is Active: {settings.is_active}')
            self.stdout.write(f'  Has Refresh Token: {bool(settings.refresh_token)}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating from_email: {e}')
            ) 