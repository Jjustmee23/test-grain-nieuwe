from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Device, DevicePowerStatus, PowerEvent
from mill.services.unified_power_management_service import UnifiedPowerManagementService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for suspicious activity (production without power) across all devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-interval',
            type=int,
            default=5,
            help='Check interval in minutes (default: 5)'
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Check specific device only'
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Check devices in specific factory only'
        )
        parser.add_argument(
            '--create-events',
            action='store_true',
            help='Create power events for suspicious activity'
        )

    def handle(self, *args, **options):
        check_interval = options['check_interval']
        device_id = options['device_id']
        factory_id = options['factory_id']
        create_events = options['create_events']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting suspicious activity check with {check_interval}-minute interval...')
        )
        
        # Get devices to check
        devices = Device.objects.all()
        
        if device_id:
            devices = devices.filter(id=device_id)
        elif factory_id:
            devices = devices.filter(factory_id=factory_id)
        
        if not devices.exists():
            self.stdout.write(
                self.style.WARNING('No devices found matching the criteria.')
            )
            return
        
        # Initialize service
        service = UnifiedPowerManagementService()
        
        suspicious_count = 0
        checked_count = 0
        
        for device in devices:
            try:
                self.stdout.write(f'Checking device: {device.name} ({device.id})')
                
                # Get suspicious activity analysis
                analysis = service.get_suspicious_activity_analysis(device, check_interval)
                
                checked_count += 1
                
                if analysis['has_suspicious_activity']:
                    suspicious_count += 1
                    
                    self.stdout.write(
                        self.style.ERROR(f'  CRITICAL: {analysis["message"]}')
                    )
                    
                    # Create power event if requested
                    if create_events:
                        self._create_suspicious_activity_event(device, analysis)
                        
                elif analysis['pending_check']:
                    self.stdout.write(
                        self.style.WARNING(f'  PENDING: {analysis["message"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  NORMAL: {analysis["message"]}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error checking device {device.name}: {str(e)}')
                )
                logger.error(f'Error checking suspicious activity for device {device.id}: {str(e)}')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Check completed: {checked_count} devices checked')
        )
        
        if suspicious_count > 0:
            self.stdout.write(
                self.style.ERROR(f'CRITICAL: {suspicious_count} devices with suspicious activity detected!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No suspicious activity detected.')
            )
    
    def _create_suspicious_activity_event(self, device, analysis):
        """Create a power event for suspicious activity"""
        try:
            # Check if event already exists for this device and time period
            existing_event = PowerEvent.objects.filter(
                device=device,
                event_type='production_without_power',
                created_at__gte=timezone.now() - timezone.timedelta(minutes=10)
            ).first()
            
            if existing_event:
                self.stdout.write(f'  Event already exists for device {device.name}')
                return
            
            # Create new event
            event = PowerEvent.objects.create(
                device=device,
                event_type='production_without_power',
                severity='critical',
                ain1_value=0.0,  # No power
                message=f"CRITICAL: {analysis['analysis_data']['total_production']} bags produced during {analysis['analysis_data']['check_interval_minutes']}-minute no-power period!",
                notification_sent=False,
                email_sent=False,
                super_admin_notified=False
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'  Created power event: {event.id}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Error creating event: {str(e)}')
            )
            logger.error(f'Error creating suspicious activity event for device {device.id}: {str(e)}') 