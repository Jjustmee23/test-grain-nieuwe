from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Device, RawData, DevicePowerStatus, PowerEvent, Factory
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Migrate counter data to testdb and populate power management data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of historical data to generate'
        )
        parser.add_argument(
            '--devices',
            type=int,
            default=10,
            help='Number of devices to create'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data migration...'))
        
        days = options['days']
        num_devices = options['devices']
        
        # Get or create factories
        factories = self.get_or_create_factories()
        
        # Create devices and populate data
        devices = self.create_devices_and_data(factories, num_devices, days)
        
        # Create power status records
        self.create_power_status_records(devices)
        
        # Create some power events for demonstration
        self.create_sample_power_events(devices)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully migrated data: {len(devices)} devices, {days} days of data'
            )
        )

    def get_or_create_factories(self):
        """Get or create sample factories"""
        factory_names = [
            'مطحنة المتحدة 1',
            'مطحنة نور السبطين 1', 
            'مطحنة دستار 2',
            'مطحنة النجف',
            'مطحنة الكوفة',
            'مطحنة الحلة',
            'مطحنة الديوانية',
            'مطحنة الناصرية'
        ]
        
        factories = []
        for name in factory_names:
            factory, created = Factory.objects.get_or_create(
                name=name,
                defaults={
                    'status': True,
                    'group': 'Public'
                }
            )
            factories.append(factory)
            if created:
                self.stdout.write(f'Created factory: {name}')
        
        return factories

    def create_devices_and_data(self, factories, num_devices, days):
        """Create devices and populate with historical data"""
        devices = []
        
        for i in range(num_devices):
            # Select random factory
            factory = random.choice(factories)
            
            # Create device
            device_name = f'Device_{i+1:03d}'
            device, created = Device.objects.get_or_create(
                id=device_name,
                defaults={
                    'name': device_name,
                    'factory': factory,
                    'status': True,
                    'selected_counter': 'counter_1'
                }
            )
            devices.append(device)
            
            if created:
                self.stdout.write(f'Created device: {device_name} in {factory.name}')
            
            # Generate historical data
            self.generate_device_data(device, days)
        
        return devices

    def generate_device_data(self, device, days):
        """Generate historical data for a device"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        counter_1 = random.randint(1000, 5000)  # Starting counter value
        
        while current_date <= end_date:
            # Generate multiple entries per day (every 2 hours)
            for hour in range(0, 24, 2):
                timestamp = current_date.replace(hour=hour, minute=random.randint(0, 59))
                
                # Generate realistic counter increments
                counter_increment = random.randint(50, 200)
                counter_1 += counter_increment
                
                # Generate power values (ain1_value)
                # Most of the time power should be on (> 0)
                if random.random() < 0.95:  # 95% of the time power is on
                    ain1_value = random.uniform(220.0, 240.0)  # Normal power range
                else:
                    ain1_value = random.uniform(0.0, 5.0)  # Power loss
                
                # Create RawData entry
                RawData.objects.create(
                    device=device,
                    timestamp=timestamp,
                    mobile_signal=random.randint(20, 100),
                    dout_enabled='enabled',
                    dout='on',
                    di_mode='input',
                    din='closed',
                    counter_1=counter_1,
                    counter_2=random.randint(0, 1000),
                    counter_3=random.randint(0, 1000),
                    counter_4=random.randint(0, 1000),
                    ain_mode='voltage',
                    ain1_value=ain1_value,  # Power value
                    ain2_value=random.uniform(0, 10),
                    ain3_value=random.uniform(0, 10),
                    ain4_value=random.uniform(0, 10),
                    ain5_value=random.uniform(0, 10),
                    ain6_value=random.uniform(0, 10),
                    ain7_value=random.uniform(0, 10),
                    ain8_value=random.uniform(0, 10),
                    start_flag=1,
                    type=1,
                    length=100,
                    version=1,
                    end_flag=1
                )
            
            current_date += timedelta(days=1)

    def create_power_status_records(self, devices):
        """Create power status records for all devices"""
        for device in devices:
            # Get the latest raw data for this device
            latest_data = RawData.objects.filter(device=device).order_by('-timestamp').first()
            
            if latest_data:
                # Create or update power status
                power_status, created = DevicePowerStatus.objects.get_or_create(
                    device=device,
                    defaults={
                        'has_power': latest_data.ain1_value > 0.0,
                        'ain1_value': latest_data.ain1_value,
                        'power_threshold': 0.0,
                        'last_power_check': latest_data.timestamp
                    }
                )
                
                if not created:
                    # Update existing record
                    power_status.has_power = latest_data.ain1_value > 0.0
                    power_status.ain1_value = latest_data.ain1_value
                    power_status.last_power_check = latest_data.timestamp
                    power_status.save()
                
                if created:
                    self.stdout.write(f'Created power status for device: {device.name}')

    def create_sample_power_events(self, devices):
        """Create some sample power events for demonstration"""
        event_types = ['power_loss', 'power_restored', 'production_without_power']
        severities = ['low', 'medium', 'high', 'critical']
        
        for device in devices:
            # Create 1-3 random events per device
            num_events = random.randint(1, 3)
            
            for i in range(num_events):
                # Random event date within last 7 days
                event_date = timezone.now() - timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                event_type = random.choice(event_types)
                severity = random.choice(severities)
                
                # Get random raw data for this device
                raw_data = RawData.objects.filter(device=device).order_by('?').first()
                
                if raw_data:
                    # Create power event
                    PowerEvent.objects.create(
                        device=device,
                        event_type=event_type,
                        severity=severity,
                        ain1_value=raw_data.ain1_value,
                        counter_1_value=raw_data.counter_1,
                        counter_2_value=raw_data.counter_2,
                        counter_3_value=raw_data.counter_3,
                        counter_4_value=raw_data.counter_4,
                        message=f'Sample {event_type.replace("_", " ")} event for {device.name}',
                        created_at=event_date
                    )
        
        self.stdout.write('Created sample power events') 