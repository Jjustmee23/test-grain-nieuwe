from django.core.management.base import BaseCommand
from mill.models import Device, DevicePowerStatus, RawData
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create missing DevicePowerStatus records for all devices'

    def handle(self, *args, **options):
        self.stdout.write('Creating missing DevicePowerStatus records...')
        
        devices = Device.objects.all()
        created_count = 0
        updated_count = 0
        
        for device in devices:
            try:
                # Get or create power status
                power_status, created = DevicePowerStatus.objects.get_or_create(
                    device=device,
                    defaults={'power_threshold': 0.0}
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✅ Created power status for: {device.name}')
                else:
                    # Update existing record with latest data
                    latest_raw_data = RawData.objects.filter(
                        device=device,
                        ain1_value__isnull=False
                    ).order_by('-timestamp').first()
                    
                    if latest_raw_data:
                        power_status.ain1_value = latest_raw_data.ain1_value
                        power_status.last_power_check = latest_raw_data.timestamp
                        power_status.has_power = latest_raw_data.ain1_value > 0
                        power_status.save()
                        updated_count += 1
                        self.stdout.write(f'  🔄 Updated power status for: {device.name}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error processing {device.name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'  Created: {created_count} new records')
        self.stdout.write(f'  Updated: {updated_count} existing records')
        self.stdout.write(f'  Total devices: {devices.count()}') 