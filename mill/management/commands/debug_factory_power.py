from django.core.management.base import BaseCommand
from mill.models import Factory, Device, DevicePowerStatus
from mill.services.unified_power_management_service import UnifiedPowerManagementService
from django.utils import timezone

class Command(BaseCommand):
    help = 'Debug factory power overview functionality'

    def add_arguments(self, parser):
        parser.add_argument('factory_id', type=int, help='Factory ID to debug')

    def handle(self, *args, **options):
        factory_id = options['factory_id']
        
        self.stdout.write(f'=== DEBUG FACTORY POWER OVERVIEW (Factory ID: {factory_id}) ===\n')
        
        try:
            # Get factory
            factory = Factory.objects.get(id=factory_id)
            self.stdout.write(f'1. Factory: {factory.name}')
            
            # Get devices
            devices = Device.objects.filter(factory=factory)
            self.stdout.write(f'2. Devices in factory: {devices.count()}')
            
            for device in devices:
                self.stdout.write(f'   - {device.name}')
            
            # Ensure all devices have DevicePowerStatus records
            self.stdout.write('\n3. Ensuring DevicePowerStatus records:')
            for device in devices:
                power_status, created = DevicePowerStatus.objects.get_or_create(
                    device=device,
                    defaults={'power_threshold': 0.0}
                )
                
                if created:
                    self.stdout.write(f'   ✅ Created power status for: {device.name}')
                else:
                    self.stdout.write(f'   ✅ Power status exists for: {device.name}')
            
            # Get power summary
            self.stdout.write('\n4. Getting power summary:')
            service = UnifiedPowerManagementService()
            power_summary = service.get_device_power_summary(factory_id=factory_id)
            self.stdout.write(f'   Power summary keys: {list(power_summary.keys())}')
            
            # Get actual DevicePowerStatus objects
            self.stdout.write('\n5. Getting DevicePowerStatus objects:')
            power_statuses = []
            for device in devices:
                power_status = DevicePowerStatus.objects.filter(device=device).first()
                if power_status:
                    power_statuses.append(power_status)
                    self.stdout.write(f'   ✅ {device.name}: last_check={power_status.last_power_check}, has_power={power_status.has_power}, ain1={power_status.ain1_value}')
                else:
                    self.stdout.write(f'   ❌ {device.name}: No power status found')
            
            self.stdout.write(f'\n6. Total power statuses: {len(power_statuses)}')
            
            # Test template context
            self.stdout.write('\n7. Template context test:')
            for power_status in power_statuses:
                self.stdout.write(f'   Device: {power_status.device.name}')
                self.stdout.write(f'   - power_status.last_power_check: {power_status.last_power_check}')
                self.stdout.write(f'   - power_status.has_power: {power_status.has_power}')
                self.stdout.write(f'   - power_status.ain1_value: {power_status.ain1_value}')
                self.stdout.write('')
            
        except Factory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Factory with ID {factory_id} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
        
        self.stdout.write('=== DEBUG COMPLETED ===') 