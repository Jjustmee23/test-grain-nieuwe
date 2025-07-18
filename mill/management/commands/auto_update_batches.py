from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from mill.models import Batch, ProductionData, Device
from django.db.models import Max
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Auto-update batch progress using latest ProductionData'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-id',
            type=int,
            help='Update specific batch by ID',
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Update all batches for a specific factory',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        batch_id = options.get('batch_id')
        factory_id = options.get('factory_id')
        dry_run = options.get('dry_run')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get batches to update
        if batch_id:
            batches = Batch.objects.filter(id=batch_id)
        elif factory_id:
            batches = Batch.objects.filter(factory_id=factory_id)
        else:
            batches = Batch.objects.filter(status__in=['approved', 'in_process', 'paused'])

        if not batches.exists():
            self.stdout.write(self.style.WARNING('No batches found to update'))
            return

        self.stdout.write(f"Found {batches.count()} batches to update")

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for batch in batches:
            try:
                if self.update_batch_progress(batch, dry_run):
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Updated batch {batch.batch_number} - "
                            f"Progress: {batch.progress_percentage:.1f}% "
                            f"(Current: {batch.current_value}, Expected: {batch.expected_flour_output})"
                        )
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"- Skipped batch {batch.batch_number} - No production data available"
                        )
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error updating batch {batch.batch_number}: {str(e)}")
                )
                logger.error(f"Error updating batch {batch.batch_number}: {str(e)}")

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("UPDATE SUMMARY:")
        self.stdout.write(f"Total batches processed: {batches.count()}")
        self.stdout.write(f"Successfully updated: {updated_count}")
        self.stdout.write(f"Skipped (no data): {skipped_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No actual changes were made"))

    def update_batch_progress(self, batch, dry_run=False):
        """
        Update batch progress using the latest ProductionData
        """
        if not batch.factory:
            self.stdout.write(f"  - Batch {batch.batch_number} has no factory")
            return False

        # Get devices for this factory
        devices = Device.objects.filter(factory=batch.factory)
        if not devices.exists():
            self.stdout.write(f"  - Factory {batch.factory.name} has no devices")
            return False

        # Get the latest ProductionData for each device
        latest_production_data = []
        for device in devices:
            # Get the most recent ProductionData for this device
            latest_data = ProductionData.objects.filter(device=device).order_by('-updated_at').first()
            if latest_data:
                latest_production_data.append(latest_data)

        if not latest_production_data:
            self.stdout.write(f"  - No ProductionData found for factory {batch.factory.name}")
            return False

        # Calculate total current production from all devices
        total_current_production = sum(data.daily_production for data in latest_production_data)
        
        # Calculate batch progress
        # The batch current_value should be the difference since batch start
        # Since ProductionData.daily_production represents the current daily production
        # We need to calculate the cumulative production since batch start
        
        # Get the latest updated_at timestamp to know when this data was last updated
        latest_update_time = max(data.updated_at for data in latest_production_data)
        
        # For now, we'll use the daily_production as the current value
        # This assumes the daily_production represents the current counter value
        new_current_value = total_current_production
        
        # Calculate actual flour output based on current production
        # Assuming 1 unit of production = 1 kg of flour (adjust as needed)
        from decimal import Decimal
        actual_flour_output = Decimal(str(new_current_value)) / Decimal('1000')  # Convert to tons
        
        if not dry_run:
            with transaction.atomic():
                # Update batch values
                batch.current_value = new_current_value
                batch.actual_flour_output = actual_flour_output
                
                # Check if batch is 100% complete
                if batch.progress_percentage >= 100 and batch.status != 'completed':
                    batch.status = 'completed'
                    batch.is_completed = True
                    batch.end_date = timezone.now()
                    self.stdout.write(f"  - Batch {batch.batch_number} marked as completed!")
                
                batch.save()
                
                # Log the update
                logger.info(
                    f"Batch {batch.batch_number} updated - "
                    f"Current: {new_current_value}, "
                    f"Actual Output: {actual_flour_output:.2f} tons, "
                    f"Progress: {batch.progress_percentage:.1f}%, "
                    f"Last Update: {latest_update_time}"
                )
        else:
            # Dry run - just show what would be updated
            self.stdout.write(f"  - Would update batch {batch.batch_number}:")
            self.stdout.write(f"    Current value: {batch.current_value} → {new_current_value}")
            self.stdout.write(f"    Actual output: {batch.actual_flour_output} → {actual_flour_output:.2f} tons")
            self.stdout.write(f"    Progress: {batch.progress_percentage:.1f}%")
            self.stdout.write(f"    Latest data from: {latest_update_time}")

        return True 