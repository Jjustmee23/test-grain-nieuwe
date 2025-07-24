from django.core.management.base import BaseCommand
from mill.models import Device, PowerData, RawData, Factory
from django.db.models import Count, Max, Min, Avg


class Command(BaseCommand):
    help = 'Check power data and RawData for devices'

    def add_arguments(self, parser):
        parser.add_argument('--factory-id', type=int, help='Check specific factory')
        parser.add_argument('--device-id', type=int, help='Check specific device')

    def handle(self, *args, **options):
        self.stdout.write("Checking power data...")
        
        factory_id = options.get('factory_id')
        device_id = options.get('device_id')
        
        devices = Device.objects.all()
        
        if factory_id:
            devices = devices.filter(factory_id=factory_id)
            self.stdout.write(f"Checking factory ID: {factory_id}")
        
        if device_id:
            devices = devices.filter(id=device_id)
            self.stdout.write(f"Checking device ID: {device_id}")
        
        self.stdout.write(f"Total devices to check: {devices.count()}")
        
        # Check PowerData
        self.stdout.write("\n=== PowerData Analysis ===")
        power_data_count = PowerData.objects.filter(device__in=devices).count()
        self.stdout.write(f"PowerData records: {power_data_count}")
        
        power_data_with_ain1 = PowerData.objects.filter(
            device__in=devices,
            ain1_value__isnull=False
        ).count()
        self.stdout.write(f"PowerData with AIN1 values: {power_data_with_ain1}")
        
        # Check RawData
        self.stdout.write("\n=== RawData Analysis ===")
        raw_data_count = RawData.objects.filter(device__in=devices).count()
        self.stdout.write(f"RawData records: {raw_data_count}")
        
        raw_data_with_ain1 = RawData.objects.filter(
            device__in=devices,
            ain1_value__isnull=False
        ).count()
        self.stdout.write(f"RawData with AIN1 values: {raw_data_with_ain1}")
        
        # Sample data
        self.stdout.write("\n=== Sample Data ===")
        for device in devices[:5]:
            self.stdout.write(f"\nDevice: {device.name} (ID: {device.id})")
            
            # PowerData
            power_data = PowerData.objects.filter(device=device).first()
            if power_data:
                self.stdout.write(f"  PowerData: AIN1={power_data.ain1_value}, Has Power={power_data.has_power}")
            else:
                self.stdout.write("  PowerData: No record")
            
            # RawData
            latest_raw = RawData.objects.filter(
                device=device,
                ain1_value__isnull=False
            ).order_by('-timestamp').first()
            
            if latest_raw:
                self.stdout.write(f"  RawData: AIN1={latest_raw.ain1_value}, Timestamp={latest_raw.timestamp}")
            else:
                self.stdout.write("  RawData: No AIN1 data")
        
        # Statistics
        if raw_data_with_ain1 > 0:
            ain1_stats = RawData.objects.filter(
                device__in=devices,
                ain1_value__isnull=False
            ).aggregate(
                min_ain1=Min('ain1_value'),
                max_ain1=Max('ain1_value'),
                avg_ain1=Avg('ain1_value')
            )
            
            self.stdout.write(f"\n=== AIN1 Statistics ===")
            self.stdout.write(f"Min AIN1: {ain1_stats['min_ain1']}")
            self.stdout.write(f"Max AIN1: {ain1_stats['max_ain1']}")
            self.stdout.write(f"Avg AIN1: {ain1_stats['avg_ain1']}")
        
        self.stdout.write(self.style.SUCCESS("Power data check completed!")) 