from django.core.management.base import BaseCommand
from mill.models import Device, RawData, DevicePowerStatus, PowerEvent

class Command(BaseCommand):
    help = 'Remove all test devices and their data, keeping only real devices'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting cleanup of test data...'))
        
        # Find all test devices (Device_001, Device_002, etc.)
        test_devices = Device.objects.filter(id__startswith='Device_')
        
        if test_devices.exists():
            self.stdout.write(f'Found {test_devices.count()} test devices to remove:')
            for device in test_devices:
                self.stdout.write(f'  - {device.id} ({device.name})')
            
            # Remove related data
            device_ids = list(test_devices.values_list('id', flat=True))
            
            # Remove RawData
            raw_data_count = RawData.objects.filter(device_id__in=device_ids).count()
            RawData.objects.filter(device_id__in=device_ids).delete()
            self.stdout.write(f'Removed {raw_data_count} RawData records')
            
            # Remove PowerEvents
            power_events_count = PowerEvent.objects.filter(device_id__in=device_ids).count()
            PowerEvent.objects.filter(device_id__in=device_ids).delete()
            self.stdout.write(f'Removed {power_events_count} PowerEvent records')
            
            # Remove DevicePowerStatus
            power_status_count = DevicePowerStatus.objects.filter(device_id__in=device_ids).count()
            DevicePowerStatus.objects.filter(device_id__in=device_ids).delete()
            self.stdout.write(f'Removed {power_status_count} DevicePowerStatus records')
            
            # Remove the devices themselves
            test_devices.delete()
            self.stdout.write(f'Removed {len(device_ids)} test devices')
            
        else:
            self.stdout.write('No test devices found to remove')
        
        # Show remaining devices
        remaining_devices = Device.objects.all()
        self.stdout.write(f'\nRemaining devices ({remaining_devices.count()}):')
        for device in remaining_devices:
            factory_name = device.factory.name if device.factory else 'No Factory'
            self.stdout.write(f'  - {device.id} ({device.name}) in {factory_name}')
        
        self.stdout.write(self.style.SUCCESS('Cleanup completed successfully!')) 