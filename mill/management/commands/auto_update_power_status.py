from django.core.management.base import BaseCommand
from mill.models import Device, RawData, DevicePowerStatus, PowerEvent
from mill.services.power_management_service import PowerManagementService
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically update power status for all devices based on latest ain1_value data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-events',
            action='store_true',
            help='Create power events when status changes',
        )
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Send notifications for power events',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting automatic power status update...'))
        
        power_service = PowerManagementService()
        
        # Get all devices that belong to factories
        devices = Device.objects.filter(factory__isnull=False)
        self.stdout.write(f'Checking {devices.count()} devices for power status updates...')
        
        updated_count = 0
        power_loss_events = 0
        power_restore_events = 0
        
        for device in devices:
            try:
                # Get the latest RawData entry for this device
                latest_raw_data = RawData.objects.filter(
                    device=device,
                    ain1_value__isnull=False
                ).order_by('-timestamp').first()
                
                if not latest_raw_data or latest_raw_data.ain1_value is None:
                    continue
                
                # Get or create power status
                power_status, created = DevicePowerStatus.objects.get_or_create(
                    device=device,
                    defaults={'power_threshold': 0.0}
                )
                
                # Store previous state
                previous_has_power = power_status.has_power
                
                # Update power status based on ain1_value
                # According to user: everything above 0 is power, 0 or below is no power
                power_status.ain1_value = latest_raw_data.ain1_value
                power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
                
                # Determine if device has power (anything > 0 is power)
                power_status.has_power = latest_raw_data.ain1_value > 0
                
                # Check if status changed
                status_changed = previous_has_power != power_status.has_power
                
                if status_changed:
                    if not power_status.has_power:
                        # Power loss detected
                        power_status.power_loss_detected_at = latest_raw_data.timestamp or timezone.now()
                        power_status.power_restored_at = None
                        power_loss_events += 1
                        
                        if not options['dry_run']:
                            self.stdout.write(f'  🔴 Power LOST: {device.name} (ain1_value={latest_raw_data.ain1_value})')
                            
                            if options['create_events']:
                                # Create power loss event
                                event = PowerEvent.objects.create(
                                    device=device,
                                    event_type='power_loss',
                                    severity='high',
                                    ain1_value=latest_raw_data.ain1_value,
                                    counter_1_value=latest_raw_data.counter_1,
                                    counter_2_value=latest_raw_data.counter_2,
                                    counter_3_value=latest_raw_data.counter_3,
                                    counter_4_value=latest_raw_data.counter_4,
                                    message=f"Power loss detected on device {device.name}. AIN1 value: {latest_raw_data.ain1_value}"
                                )
                                
                                if options['send_notifications']:
                                    power_service._handle_power_loss(device, latest_raw_data.ain1_value, latest_raw_data)
                        else:
                            self.stdout.write(f'  🔴 Would detect power loss: {device.name} (ain1_value={latest_raw_data.ain1_value})')
                            
                    else:
                        # Power restored
                        power_status.power_restored_at = latest_raw_data.timestamp or timezone.now()
                        power_restore_events += 1
                        
                        if not options['dry_run']:
                            self.stdout.write(f'  🟢 Power RESTORED: {device.name} (ain1_value={latest_raw_data.ain1_value})')
                            
                            if options['create_events']:
                                # Create power restore event
                                event = PowerEvent.objects.create(
                                    device=device,
                                    event_type='power_restored',
                                    severity='medium',
                                    ain1_value=latest_raw_data.ain1_value,
                                    counter_1_value=latest_raw_data.counter_1,
                                    counter_2_value=latest_raw_data.counter_2,
                                    counter_3_value=latest_raw_data.counter_3,
                                    counter_4_value=latest_raw_data.counter_4,
                                    message=f"Power restored on device {device.name}. AIN1 value: {latest_raw_data.ain1_value}"
                                )
                                
                                if options['send_notifications']:
                                    power_service._handle_power_restore(device, latest_raw_data.ain1_value, latest_raw_data)
                        else:
                            self.stdout.write(f'  🟢 Would detect power restore: {device.name} (ain1_value={latest_raw_data.ain1_value})')
                
                # Check for production without power
                if not power_status.has_power:
                    counter_values = {
                        'counter_1': latest_raw_data.counter_1,
                        'counter_2': latest_raw_data.counter_2,
                        'counter_3': latest_raw_data.counter_3,
                        'counter_4': latest_raw_data.counter_4,
                    }
                    
                    production_without_power = power_status.check_production_without_power(counter_values)
                    
                    if production_without_power and not options['dry_run']:
                        self.stdout.write(f'  ⚠️  CRITICAL: Production without power detected: {device.name}')
                        
                        if options['create_events']:
                            event = PowerEvent.objects.create(
                                device=device,
                                event_type='production_without_power',
                                severity='critical',
                                ain1_value=latest_raw_data.ain1_value,
                                counter_1_value=latest_raw_data.counter_1,
                                counter_2_value=latest_raw_data.counter_2,
                                counter_3_value=latest_raw_data.counter_3,
                                counter_4_value=latest_raw_data.counter_4,
                                message=f"CRITICAL: Production detected without power on device {device.name}. This indicates a serious system issue."
                            )
                            
                            if options['send_notifications']:
                                power_service._handle_production_without_power(device, latest_raw_data.ain1_value, latest_raw_data)
                
                if not options['dry_run']:
                    power_status.save()
                    updated_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating power status for device {device.name}: {str(e)}'))
                continue
        
        # Summary
        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'DRY RUN - No changes made'))
            self.stdout.write(f'Would update {updated_count} devices')
            self.stdout.write(f'Would detect {power_loss_events} power loss events')
            self.stdout.write(f'Would detect {power_restore_events} power restore events')
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated power status for {updated_count} devices'))
            if power_loss_events > 0:
                self.stdout.write(self.style.WARNING(f'Detected {power_loss_events} power loss events'))
            if power_restore_events > 0:
                self.stdout.write(self.style.SUCCESS(f'Detected {power_restore_events} power restore events'))
        
        # Get current power status summary
        total_devices = Device.objects.filter(factory__isnull=False).count()
        devices_with_power = DevicePowerStatus.objects.filter(
            device__factory__isnull=False, 
            has_power=True
        ).count()
        devices_without_power = DevicePowerStatus.objects.filter(
            device__factory__isnull=False, 
            has_power=False
        ).count()
        
        uptime_percentage = (devices_with_power / total_devices * 100) if total_devices > 0 else 100
        
        self.stdout.write(f'\nPower Status Summary:')
        self.stdout.write(f'  Total devices: {total_devices}')
        self.stdout.write(f'  Devices with power: {devices_with_power}')
        self.stdout.write(f'  Devices without power: {devices_without_power}')
        self.stdout.write(f'  System uptime: {uptime_percentage:.1f}%')
        
        self.stdout.write(self.style.SUCCESS('Automatic power status update completed!')) 