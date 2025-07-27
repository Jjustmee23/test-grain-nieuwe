from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Factory, Device, PowerEvent, PowerData
from datetime import timedelta
import random
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Simulate power events for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument('factory_id', type=int, help='Factory ID to simulate events for')
        parser.add_argument('--events', type=int, default=5, help='Number of events to create')
        parser.add_argument('--days', type=int, default=7, help='Spread events over this many days')

    def handle(self, *args, **options):
        factory_id = options['factory_id']
        num_events = options['events']
        days = options['days']
        
        try:
            factory = Factory.objects.get(id=factory_id)
            self.stdout.write(f"Simulating power events for factory: {factory.name} (ID: {factory_id})")
            
            # Get all devices for this factory
            devices = Device.objects.filter(factory=factory)
            if not devices.exists():
                self.stdout.write(self.style.WARNING("No devices found for this factory"))
                return
            
            self.stdout.write(f"Found {devices.count()} devices")
            
            # Create simulated events
            event_types = ['power_loss', 'power_restored', 'power_fluctuation']
            severities = ['low', 'medium', 'high']
            
            created_events = 0
            
            for i in range(num_events):
                # Select random device
                device = random.choice(devices)
                
                # Select random event type and severity
                event_type = random.choice(event_types)
                severity = random.choice(severities)
                
                # Create timestamp within the specified days
                days_ago = random.randint(0, days)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                event_time = timezone.now() - timedelta(
                    days=days_ago,
                    hours=hours_ago,
                    minutes=minutes_ago
                )
                
                # Generate realistic power values
                if event_type == 'power_loss':
                    ain1_value = 0.0
                    previous_ain1_value = random.uniform(0.1, 0.5)
                    message = f"Simulated power loss on {device.name}. Power dropped from {previous_ain1_value:.2f} kW to 0 kW"
                    is_resolved = random.choice([True, False])
                elif event_type == 'power_restored':
                    ain1_value = random.uniform(0.1, 0.5)
                    previous_ain1_value = 0.0
                    message = f"Simulated power restore on {device.name}. Power restored to {ain1_value:.2f} kW"
                    is_resolved = True
                else:  # power_fluctuation
                    ain1_value = random.uniform(0.05, 0.3)
                    previous_ain1_value = random.uniform(0.1, 0.4)
                    message = f"Simulated power fluctuation on {device.name}. Power changed from {previous_ain1_value:.2f} kW to {ain1_value:.2f} kW"
                    is_resolved = random.choice([True, False])
                
                # Create the event
                event = PowerEvent.objects.create(
                    device=device,
                    event_type=event_type,
                    severity=severity,
                    ain1_value=ain1_value,
                    previous_ain1_value=previous_ain1_value,
                    message=message,
                    is_resolved=is_resolved,
                    created_at=event_time
                )
                
                created_events += 1
                self.stdout.write(f"  Created {event_type} event ({severity}) for {device.name} at {event_time}")
            
            self.stdout.write(f"\nCreated {created_events} simulated power events")
            
            # Show summary
            total_events = PowerEvent.objects.filter(device__factory=factory).count()
            recent_events = PowerEvent.objects.filter(
                device__factory=factory,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            unresolved_events = PowerEvent.objects.filter(
                device__factory=factory,
                is_resolved=False
            ).count()
            
            self.stdout.write(f"\nEvent Summary:")
            self.stdout.write(f"  Total events: {total_events}")
            self.stdout.write(f"  Recent events (24h): {recent_events}")
            self.stdout.write(f"  Unresolved events: {unresolved_events}")
            
            self.stdout.write(self.style.SUCCESS("Power event simulation completed"))
            
        except Factory.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Factory with ID {factory_id} does not exist"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in simulate_power_events command: {e}") 