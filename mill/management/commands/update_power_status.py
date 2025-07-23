from django.core.management.base import BaseCommand
from mill.models import Device, RawData, DevicePowerStatus
from mill.services.power_management_service import PowerManagementService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update power status for all devices based on latest ain1_value data from database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=str,
            help='Update power status for a specific device ID',
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Update power status for all devices in a specific factory',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if no new data is available',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting power status update...'))
        
        power_service = PowerManagementService()
        
        if options['device_id']:
            # Update specific device
            try:
                device = Device.objects.get(id=options['device_id'])
                self.update_device_power_status(device, power_service, options['verbose'])
            except Device.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Device with ID {options["device_id"]} not found'))
                return
        elif options['factory_id']:
            # Update all devices in specific factory
            devices = Device.objects.filter(factory_id=options['factory_id'])
            if not devices.exists():
                self.stdout.write(self.style.ERROR(f'No devices found for factory ID {options["factory_id"]}'))
                return
            
            self.stdout.write(f'Updating power status for {devices.count()} devices in factory {options["factory_id"]}')
            for device in devices:
                self.update_device_power_status(device, power_service, options['verbose'])
        else:
            # Update all devices
            devices = Device.objects.filter(factory__isnull=False)
            self.stdout.write(f'Updating power status for {devices.count()} devices')
            
            updated_count = 0
            for device in devices:
                if self.update_device_power_status(device, power_service, options['verbose']):
                    updated_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Updated power status for {updated_count} devices'))

    def update_device_power_status(self, device, power_service, verbose=False):
        """Update power status for a specific device"""
        try:
            # Get the latest RawData entry for this device
            latest_raw_data = RawData.objects.filter(
                device=device,
                ain1_value__isnull=False
            ).order_by('-timestamp').first()
            
            if not latest_raw_data:
                if verbose:
                    self.stdout.write(f'  ⚠️  No RawData found for device {device.name}')
                return False
            
            if latest_raw_data.ain1_value is None:
                if verbose:
                    self.stdout.write(f'  ⚠️  No ain1_value data for device {device.name}')
                return False
            
            # Get or create power status
            power_status, created = DevicePowerStatus.objects.get_or_create(
                device=device,
                defaults={'power_threshold': 0.0}
            )
            
            # Store previous state
            previous_has_power = power_status.has_power
            previous_ain1_value = power_status.ain1_value
            
            # Update power status based on ain1_value
            # According to user: everything above 0 is power, 0 or below is no power
            # 0.0001 is also power
            power_status.ain1_value = latest_raw_data.ain1_value
            power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
            
            # Determine if device has power (anything > 0 is power)
            power_status.has_power = latest_raw_data.ain1_value > 0
            
            # Handle power loss
            if not power_status.has_power and previous_has_power:
                power_status.power_loss_detected_at = latest_raw_data.timestamp or timezone.now()
                power_status.power_restored_at = None
                
                if verbose:
                    self.stdout.write(f'  🔴 Power LOST for {device.name}: ain1_value={latest_raw_data.ain1_value}')
                
            # Handle power restoration
            elif power_status.has_power and not previous_has_power:
                power_status.power_restored_at = latest_raw_data.timestamp or timezone.now()
                
                if verbose:
                    self.stdout.write(f'  🟢 Power RESTORED for {device.name}: ain1_value={latest_raw_data.ain1_value}')
            
            power_status.save()
            
            if verbose:
                if power_status.has_power:
                    self.stdout.write(f'  ✅ {device.name}: Power ON (ain1_value={latest_raw_data.ain1_value})')
                else:
                    self.stdout.write(f'  ❌ {device.name}: Power OFF (ain1_value={latest_raw_data.ain1_value})')
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating power status for device {device.name}: {str(e)}'))
            return False 