from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Factory, PowerEvent, Device
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check power events for a specific factory'

    def add_arguments(self, parser):
        parser.add_argument('factory_id', type=int, help='Factory ID to check')
        parser.add_argument('--create-test-events', action='store_true', help='Create test power events')

    def handle(self, *args, **options):
        factory_id = options['factory_id']
        create_test_events = options['create_test_events']
        
        try:
            factory = Factory.objects.get(id=factory_id)
            self.stdout.write(f"Checking power events for factory: {factory.name} (ID: {factory_id})")
            
            # Get all devices for this factory
            devices = Device.objects.filter(factory=factory)
            self.stdout.write(f"Found {devices.count()} devices for factory {factory.name}")
            
            # Check all power events for this factory
            all_events = PowerEvent.objects.filter(device__factory=factory)
            self.stdout.write(f"Total power events for factory: {all_events.count()}")
            
            # Check recent events (last 24 hours)
            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
            recent_events = PowerEvent.objects.filter(
                device__factory=factory,
                created_at__gte=twenty_four_hours_ago
            )
            self.stdout.write(f"Recent events (last 24h): {recent_events.count()}")
            
            # Check unresolved events
            unresolved_events = PowerEvent.objects.filter(
                device__factory=factory,
                is_resolved=False
            )
            self.stdout.write(f"Unresolved events: {unresolved_events.count()}")
            
            # Show recent events details
            if recent_events.exists():
                self.stdout.write("\nRecent Power Events:")
                for event in recent_events.order_by('-created_at')[:10]:
                    self.stdout.write(f"  - {event.device.name}: {event.event_type} ({event.severity}) - {event.created_at}")
            else:
                self.stdout.write("\nNo recent power events found")
            
            # Show unresolved events details
            if unresolved_events.exists():
                self.stdout.write("\nUnresolved Power Events:")
                for event in unresolved_events.order_by('-created_at')[:5]:
                    self.stdout.write(f"  - {event.device.name}: {event.event_type} ({event.severity}) - {event.created_at}")
            else:
                self.stdout.write("\nNo unresolved power events found")
            
            # Create test events if requested
            if create_test_events:
                self.stdout.write("\nCreating test power events...")
                for device in devices:
                    # Create a power loss event
                    power_loss_event = PowerEvent.objects.create(
                        device=device,
                        event_type='power_loss',
                        severity='medium',
                        ain1_value=0.0,
                        previous_ain1_value=0.11,
                        message=f"Test power loss event for {device.name}",
                        is_resolved=False
                    )
                    self.stdout.write(f"  Created power loss event for {device.name}")
                    
                    # Create a power restored event
                    power_restore_event = PowerEvent.objects.create(
                        device=device,
                        event_type='power_restored',
                        severity='low',
                        ain1_value=0.11,
                        previous_ain1_value=0.0,
                        message=f"Test power restore event for {device.name}",
                        is_resolved=True
                    )
                    self.stdout.write(f"  Created power restore event for {device.name}")
                
                self.stdout.write("Test events created successfully")
            
            # Check events by type
            self.stdout.write("\nEvents by type:")
            for event_type, _ in PowerEvent.EVENT_TYPES:
                count = all_events.filter(event_type=event_type).count()
                self.stdout.write(f"  {event_type}: {count}")
            
            # Check events by severity
            self.stdout.write("\nEvents by severity:")
            for severity, _ in PowerEvent.SEVERITY_LEVELS:
                count = all_events.filter(severity=severity).count()
                self.stdout.write(f"  {severity}: {count}")
            
            self.stdout.write(self.style.SUCCESS("Power events check completed"))
            
        except Factory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Factory with ID {factory_id} does not exist"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in check_power_events command: {e}") 