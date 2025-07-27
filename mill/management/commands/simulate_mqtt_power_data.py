from django.core.management.base import BaseCommand
from mill.models import Device, PowerData
from django.utils import timezone
import random
import time


class Command(BaseCommand):
    help = 'Simulate MQTT power data updates for testing PowerData system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duration to run simulation in seconds (default: 60)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Interval between updates in seconds (default: 5)',
        )
        parser.add_argument(
            '--device-id',
            type=int,
            help='Specific device ID to simulate (optional)',
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        device_id = options['device_id']
        
        if device_id:
            devices = Device.objects.filter(id=device_id)
            if not devices.exists():
                self.stdout.write(self.style.ERROR(f'Device with ID {device_id} not found'))
                return
        else:
            devices = Device.objects.all()
        
        self.stdout.write(f"Starting MQTT simulation for {devices.count()} devices")
        self.stdout.write(f"Duration: {duration} seconds, Interval: {interval} seconds")
        
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(seconds=duration)
        update_count = 0
        
        try:
            while timezone.now() < end_time:
                for device in devices:
                    # Get or create PowerData for this device
                    power_data, created = PowerData.objects.get_or_create(
                        device=device,
                        defaults={
                            'has_power': True,
                            'power_threshold': 0.0,
                        }
                    )
                    
                    # Simulate MQTT data
                    mqtt_data = {
                        'ain1': random.uniform(0, 100),  # Power consumption
                        'ain2': random.uniform(0, 50),   # Voltage
                        'ain3': random.uniform(0, 20),   # Current
                        'ain4': random.uniform(0, 10),   # Temperature
                    }
                    
                    # Update PowerData with MQTT data
                    power_data.update_from_mqtt(mqtt_data)
                    update_count += 1
                    
                    self.stdout.write(
                        f"Updated {device.name}: AIN1={mqtt_data['ain1']:.2f}, "
                        f"Power={'ON' if power_data.has_power else 'OFF'}, "
                        f"Losses today: {power_data.power_loss_count_today}"
                    )
                
                # Wait for next interval
                if timezone.now() + timezone.timedelta(seconds=interval) < end_time:
                    time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nSimulation interrupted by user"))
        
        total_time = timezone.now() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'Simulation completed. '
                f'Total updates: {update_count}, '
                f'Duration: {total_time.total_seconds():.1f} seconds'
            )
        ) 