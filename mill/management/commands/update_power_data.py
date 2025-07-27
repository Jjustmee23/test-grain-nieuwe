from django.core.management.base import BaseCommand
from mill.models import Device, PowerData
from mill.services.unified_power_management_service import UnifiedPowerManagementService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update power data for all devices'

    def add_arguments(self, parser):
        parser.add_argument('--factory-id', type=int, help='Update specific factory only')
        parser.add_argument('--device-id', type=str, help='Update specific device only')

    def handle(self, *args, **options):
        factory_id = options.get('factory_id')
        device_id = options.get('device_id')
        
        try:
            # Get devices to update
            devices = Device.objects.all()
            
            if factory_id:
                devices = devices.filter(factory_id=factory_id)
                self.stdout.write(f"Updating power data for factory ID: {factory_id}")
            
            if device_id:
                devices = devices.filter(id=device_id)
                self.stdout.write(f"Updating power data for device ID: {device_id}")
            
            self.stdout.write(f"Found {devices.count()} devices to update")
            
            # Update power data for each device
            updated_count = 0
            error_count = 0
            
            for device in devices:
                try:
                    # Get or create PowerData record
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
                        updated_count += 1
                        self.stdout.write(f"✓ Updated {device.name} - AIN1: {power_data.ain1_value}, Has Power: {power_data.has_power}")
                    else:
                        error_count += 1
                        self.stdout.write(f"✗ Failed to update {device.name}")
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(f"✗ Error updating {device.name}: {str(e)}")
                    logger.error(f"Error updating power data for device {device.name}: {e}")
            
            # Also run the unified service update
            self.stdout.write("\nRunning unified service update...")
            service = UnifiedPowerManagementService()
            update_result = service.update_all_devices_power_status()
            
            self.stdout.write(f"\nUpdate Summary:")
            self.stdout.write(f"  Devices updated: {updated_count}")
            self.stdout.write(f"  Errors: {error_count}")
            self.stdout.write(f"  Unified service result: {update_result}")
            
            self.stdout.write(self.style.SUCCESS("Power data update completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in update_power_data command: {e}") 