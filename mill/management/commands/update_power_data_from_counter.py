from django.core.management.base import BaseCommand
from mill.models import Device, PowerData
from django.utils import timezone


class Command(BaseCommand):
    help = 'Update PowerData from counter database mqtt_data table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Specific device ID to update (optional)',
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Update all devices in specific factory (optional)',
        )

    def handle(self, *args, **options):
        device_id = options['device_id']
        factory_id = options['factory_id']
        
        if device_id:
            devices = Device.objects.filter(id=device_id)
            if not devices.exists():
                self.stdout.write(self.style.ERROR(f'Device with ID {device_id} not found'))
                return
        elif factory_id:
            devices = Device.objects.filter(factory_id=factory_id)
            if not devices.exists():
                self.stdout.write(self.style.ERROR(f'No devices found for factory ID {factory_id}'))
                return
        else:
            devices = Device.objects.all()
        
        self.stdout.write(f"Updating PowerData for {devices.count()} devices from counter database")
        
        updated_count = 0
        created_count = 0
        error_count = 0
        
        for device in devices:
            try:
                power_data, created = PowerData.objects.get_or_create(
                    device=device,
                    defaults={
                        'has_power': True,
                        'power_threshold': 0.0,
                    }
                )
                
                # Update from counter database
                success = power_data.update_from_counter_db()
                
                if success:
                    if created:
                        created_count += 1
                        self.stdout.write(f"Created and updated PowerData for device: {device.name}")
                    else:
                        updated_count += 1
                        self.stdout.write(f"Updated PowerData for device: {device.name} - AIN1: {power_data.ain1_value}, Power: {'ON' if power_data.has_power else 'OFF'}")
                else:
                    error_count += 1
                    self.stdout.write(self.style.WARNING(f"Failed to update PowerData for device: {device.name}"))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"Error updating PowerData for device {device.name}: {e}"))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'PowerData update completed. '
                f'Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
            )
        ) 