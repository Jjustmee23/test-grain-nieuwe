from django.core.management.base import BaseCommand
from django.db import connection
from mill.models import ProductionData, Device, Factory, RawData
from django.db.models import Count, Avg, Max, Min
import json

class Command(BaseCommand):
    help = 'Analyze the ProductionData table and understand its structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Analyze only a specific factory',
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Analyze only a specific device',
        )

    def handle(self, *args, **options):
        factory_id = options.get('factory_id')
        device_id = options.get('device_id')

        self.stdout.write(
            self.style.SUCCESS('=== PRODUCTION DATA ANALYSIS ===')
        )

        # 1. Basic table statistics
        total_records = ProductionData.objects.count()
        self.stdout.write(f"Total ProductionData records: {total_records}")

        if total_records == 0:
            self.stdout.write(
                self.style.WARNING("No ProductionData records found!")
            )
            return

        # 2. Get unique devices
        devices_with_data = ProductionData.objects.values('device').distinct().count()
        self.stdout.write(f"Devices with ProductionData: {devices_with_data}")

        # 3. Show sample data structure
        sample_data = ProductionData.objects.first()
        if sample_data:
            self.stdout.write("\n=== SAMPLE RECORD STRUCTURE ===")
            self.stdout.write(f"Device: {sample_data.device.name if sample_data.device else 'None'}")
            self.stdout.write(f"Daily Production: {sample_data.daily_production}")
            self.stdout.write(f"Weekly Production: {sample_data.weekly_production}")
            self.stdout.write(f"Monthly Production: {sample_data.monthly_production}")
            self.stdout.write(f"Yearly Production: {sample_data.yearly_production}")
            self.stdout.write(f"Created At: {sample_data.created_at}")
            self.stdout.write(f"Updated At: {sample_data.updated_at}")

        # 4. Analyze data by device
        self.stdout.write("\n=== DEVICE ANALYSIS ===")
        
        # Filter by factory if specified
        filter_kwargs = {}
        if factory_id:
            filter_kwargs['device__factory_id'] = factory_id
        if device_id:
            filter_kwargs['device_id'] = device_id

        device_stats = ProductionData.objects.filter(**filter_kwargs).values(
            'device__name', 'device__factory__name'
        ).annotate(
            record_count=Count('id'),
            avg_daily=Avg('daily_production'),
            avg_weekly=Avg('weekly_production'),
            avg_monthly=Avg('monthly_production'),
            avg_yearly=Avg('yearly_production'),
            max_daily=Max('daily_production'),
            max_weekly=Max('weekly_production'),
            max_monthly=Max('monthly_production'),
            max_yearly=Max('yearly_production'),
        ).order_by('device__name')

        for stat in device_stats:
            self.stdout.write(f"\nDevice: {stat['device__name']} (Factory: {stat['device__factory__name']})")
            self.stdout.write(f"  Records: {stat['record_count']}")
            self.stdout.write(f"  Daily - Avg: {stat['avg_daily']:.2f}, Max: {stat['max_daily']}")
            self.stdout.write(f"  Weekly - Avg: {stat['avg_weekly']:.2f}, Max: {stat['max_weekly']}")
            self.stdout.write(f"  Monthly - Avg: {stat['avg_monthly']:.2f}, Max: {stat['max_monthly']}")
            self.stdout.write(f"  Yearly - Avg: {stat['avg_yearly']:.2f}, Max: {stat['max_yearly']}")

        # 5. Check for duplicate records per device
        self.stdout.write("\n=== DUPLICATE ANALYSIS ===")
        duplicates = ProductionData.objects.filter(**filter_kwargs).values(
            'device__name'
        ).annotate(
            record_count=Count('id')
        ).filter(record_count__gt=1).order_by('-record_count')

        if duplicates.exists():
            self.stdout.write("Devices with multiple ProductionData records:")
            for dup in duplicates:
                self.stdout.write(f"  {dup['device__name']}: {dup['record_count']} records")
        else:
            self.stdout.write("No duplicate records found (one record per device)")

        # 6. Compare with RawData
        self.stdout.write("\n=== COMPARISON WITH RAWDATA ===")
        total_raw_data = RawData.objects.count()
        self.stdout.write(f"Total RawData records: {total_raw_data}")

        if factory_id:
            factory_raw_data = RawData.objects.filter(device__factory_id=factory_id).count()
            self.stdout.write(f"RawData for factory {factory_id}: {factory_raw_data}")

        # 7. Show latest records
        self.stdout.write("\n=== LATEST RECORDS ===")
        latest_records = ProductionData.objects.filter(**filter_kwargs).order_by('-updated_at')[:5]
        for record in latest_records:
            self.stdout.write(f"  {record.device.name}: Updated {record.updated_at}")
            self.stdout.write(f"    Daily: {record.daily_production}, Weekly: {record.weekly_production}")
            self.stdout.write(f"    Monthly: {record.monthly_production}, Yearly: {record.yearly_production}")

        self.stdout.write(
            self.style.SUCCESS('\n=== ANALYSIS COMPLETE ===')
        ) 