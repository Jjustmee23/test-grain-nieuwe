from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Factory, Device, PowerData, RawData
from mill.services.unified_power_management_service import UnifiedPowerManagementService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check and fix power data for a specific factory'

    def add_arguments(self, parser):
        parser.add_argument('factory_id', type=int, help='Factory ID to check')
        parser.add_argument('--fix', action='store_true', help='Fix missing power data')

    def handle(self, *args, **options):
        factory_id = options['factory_id']
        fix_data = options['fix']
        
        try:
            factory = Factory.objects.get(id=factory_id)
            self.stdout.write(f"Checking power data for factory: {factory.name} (ID: {factory_id})")
            
            # Get all devices for this factory
            devices = Device.objects.filter(factory=factory)
            self.stdout.write(f"Found {devices.count()} devices for factory {factory.name}")
            
            if not devices.exists():
                self.stdout.write(self.style.WARNING("No devices found for this factory"))
                return
            
            # Check PowerData records
            power_data_records = PowerData.objects.filter(device__factory=factory)
            self.stdout.write(f"Found {power_data_records.count()} PowerData records")
            
            # Check RawData records
            raw_data_records = RawData.objects.filter(device__factory=factory)
            self.stdout.write(f"Found {raw_data_records.count()} RawData records")
            
            # Check for devices without PowerData
            devices_without_power_data = devices.exclude(power_data__isnull=False)
            self.stdout.write(f"Devices without PowerData: {devices_without_power_data.count()}")
            
            if devices_without_power_data.exists():
                self.stdout.write("Devices without PowerData:")
                for device in devices_without_power_data:
                    self.stdout.write(f"  - {device.name} (ID: {device.id})")
            
            # Check for devices without RawData
            devices_without_raw_data = devices.exclude(raw_data__isnull=False)
            self.stdout.write(f"Devices without RawData: {devices_without_raw_data.count()}")
            
            if devices_without_raw_data.exists():
                self.stdout.write("Devices without RawData:")
                for device in devices_without_raw_data:
                    self.stdout.write(f"  - {device.name} (ID: {device.id})")
            
            # Check latest RawData for each device
            self.stdout.write("\nLatest RawData for each device:")
            for device in devices:
                latest_raw_data = RawData.objects.filter(
                    device=device,
                    ain1_value__isnull=False
                ).order_by('-timestamp').first()
                
                if latest_raw_data:
                    self.stdout.write(f"  {device.name}: AIN1={latest_raw_data.ain1_value}, Timestamp={latest_raw_data.timestamp}")
                else:
                    self.stdout.write(f"  {device.name}: No RawData with AIN1 value")
            
            # Test the service
            service = UnifiedPowerManagementService()
            power_summary = service.get_device_power_summary(factory_id=factory_id)
            
            self.stdout.write(f"\nPower Summary from Service:")
            self.stdout.write(f"  Total devices: {power_summary['total_devices']}")
            self.stdout.write(f"  Devices with power: {power_summary['devices_with_power']}")
            self.stdout.write(f"  Devices without power: {power_summary['devices_without_power']}")
            self.stdout.write(f"  Power events today: {power_summary['power_events_today']}")
            self.stdout.write(f"  Unresolved events: {power_summary['unresolved_events']}")
            self.stdout.write(f"  Avg uptime today: {power_summary['avg_uptime_today']}%")
            self.stdout.write(f"  Total power consumption: {power_summary['total_power_consumption']}")
            
            # Test analytics
            analytics = service.get_power_analytics(factory_id=factory_id, days=30)
            self.stdout.write(f"\nAnalytics from Service:")
            if analytics['trends']:
                self.stdout.write(f"  Avg power consumption: {analytics['trends'].get('avg_power_consumption', 0)}")
                self.stdout.write(f"  Max power consumption: {analytics['trends'].get('max_power_consumption', 0)}")
                self.stdout.write(f"  Total power losses: {analytics['trends'].get('total_power_losses', 0)}")
                self.stdout.write(f"  Total power restores: {analytics['trends'].get('total_power_restores', 0)}")
            else:
                self.stdout.write("  No analytics data available")
            
            # Fix data if requested
            if fix_data:
                self.stdout.write("\nFixing missing PowerData records...")
                fixed_count = 0
                
                for device in devices_without_power_data:
                    # Create PowerData record
                    power_data = PowerData.objects.create(
                        device=device,
                        has_power=True,
                        power_threshold=0.0,
                        ain1_value=0.0,
                        avg_power_consumption_today=0.0,
                        peak_power_consumption_today=0.0,
                        total_power_consumption_today=0.0
                    )
                    
                    # Try to get latest AIN1 value from RawData
                    latest_raw_data = RawData.objects.filter(
                        device=device,
                        ain1_value__isnull=False
                    ).order_by('-timestamp').first()
                    
                    if latest_raw_data:
                        power_data.ain1_value = latest_raw_data.ain1_value
                        power_data.last_mqtt_update = latest_raw_data.timestamp
                        power_data.has_power = latest_raw_data.ain1_value > power_data.power_threshold
                        power_data.save()
                        self.stdout.write(f"  Created PowerData for {device.name} with AIN1={latest_raw_data.ain1_value}")
                    else:
                        self.stdout.write(f"  Created PowerData for {device.name} (no RawData available)")
                    
                    fixed_count += 1
                
                self.stdout.write(f"Fixed {fixed_count} PowerData records")
                
                # Update all devices power status
                self.stdout.write("Updating all devices power status...")
                update_result = service.update_all_devices_power_status()
                self.stdout.write(f"Update result: {update_result}")
            
            self.stdout.write(self.style.SUCCESS("Power data check completed"))
            
        except Factory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Factory with ID {factory_id} does not exist"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in check_power_data command: {e}") 