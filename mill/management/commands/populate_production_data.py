from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from mill.models import RawData, ProductionData, Device, Factory
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populate ProductionData from RawData for real statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Process only a specific factory',
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Process only a specific device',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        factory_id = options.get('factory_id')
        device_id = options.get('device_id')

        self.stdout.write(
            self.style.SUCCESS('Starting ProductionData population from RawData...')
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get devices to process
        devices_query = Device.objects.all()
        if factory_id:
            devices_query = devices_query.filter(factory_id=factory_id)
        if device_id:
            devices_query = devices_query.filter(id=device_id)

        devices = devices_query.select_related('factory')
        
        if not devices.exists():
            self.stdout.write(
                self.style.ERROR('No devices found matching the criteria')
            )
            return

        self.stdout.write(f"Processing {devices.count()} devices...")

        total_created = 0
        total_updated = 0
        total_errors = 0

        for device in devices:
            try:
                created, updated = self.process_device(device, dry_run)
                total_created += created
                total_updated += updated
                
                self.stdout.write(
                    f"✓ Device {device.name} ({device.factory.name if device.factory else 'No Factory'}): "
                    f"{created} created, {updated} updated"
                )
                
            except Exception as e:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing device {device.name}: {str(e)}")
                )
                logger.error(f"Error processing device {device.name}: {str(e)}")

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("POPULATION SUMMARY:")
        self.stdout.write(f"Devices processed: {devices.count()}")
        self.stdout.write(f"ProductionData records created: {total_created}")
        self.stdout.write(f"ProductionData records updated: {total_updated}")
        self.stdout.write(f"Errors: {total_errors}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No actual changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS("ProductionData population completed!"))

    def process_device(self, device, dry_run=False):
        """Process a single device and create/update ProductionData"""
        created_count = 0
        updated_count = 0

        # Get the latest RawData for this device
        latest_raw_data = RawData.objects.filter(device=device).order_by('-timestamp').first()
        
        if not latest_raw_data:
            self.stdout.write(f"  - No RawData found for device {device.name}")
            return 0, 0

        # Get the selected counter based on device configuration
        selected_counter = device.selected_counter
        counter_value = getattr(latest_raw_data, selected_counter, 0)
        
        if counter_value is None:
            counter_value = 0

        # Calculate time-based production data
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        # Get RawData for different time periods
        today_data = RawData.objects.filter(
            device=device,
            timestamp__date=today
        ).order_by('timestamp')

        week_data = RawData.objects.filter(
            device=device,
            timestamp__date__gte=week_start
        ).order_by('timestamp')

        month_data = RawData.objects.filter(
            device=device,
            timestamp__date__gte=month_start
        ).order_by('timestamp')

        year_data = RawData.objects.filter(
            device=device,
            timestamp__date__gte=year_start
        ).order_by('timestamp')

        # Calculate production values
        daily_production = self.calculate_production(today_data, selected_counter)
        weekly_production = self.calculate_production(week_data, selected_counter)
        monthly_production = self.calculate_production(month_data, selected_counter)
        yearly_production = self.calculate_production(year_data, selected_counter)

        # Get the latest ProductionData for this device (or create new one)
        production_data = ProductionData.objects.filter(device=device).order_by('-updated_at').first()
        
        if production_data:
            # Update existing record
            if not dry_run:
                production_data.daily_production = daily_production
                production_data.weekly_production = weekly_production
                production_data.monthly_production = monthly_production
                production_data.yearly_production = yearly_production
                production_data.save()
            updated_count += 1
        else:
            # Create new record
            if not dry_run:
                ProductionData.objects.create(
                    device=device,
                    daily_production=daily_production,
                    weekly_production=weekly_production,
                    monthly_production=monthly_production,
                    yearly_production=yearly_production,
                )
            created_count += 1

        return created_count, updated_count

    def calculate_production(self, raw_data_queryset, selected_counter):
        """Calculate production from RawData for a given time period"""
        if not raw_data_queryset.exists():
            return 0

        # Get first and last values for the period
        first_data = raw_data_queryset.first()
        last_data = raw_data_queryset.last()

        if not first_data or not last_data:
            return 0

        # Get counter values
        first_value = getattr(first_data, selected_counter, 0) or 0
        last_value = getattr(last_data, selected_counter, 0) or 0

        # Calculate production as the difference
        production = last_value - first_value
        
        # Ensure production is not negative (counter might have reset)
        if production < 0:
            production = last_value  # Assume counter reset, use current value

        return production 