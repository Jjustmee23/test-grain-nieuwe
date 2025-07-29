from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.services.batch_production_service import BatchProductionService
from mill.models import Batch
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update all batches using the new BatchProductionService (v2)'

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
        parser.add_argument(
            '--status',
            type=str,
            choices=['pending', 'approved', 'in_process', 'paused', 'stopped', 'completed', 'rejected'],
            help='Update only batches with specific status',
        )

    def handle(self, *args, **options):
        batch_id = options.get('batch_id')
        factory_id = options.get('factory_id')
        dry_run = options.get('dry_run')
        status_filter = options.get('status')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Initialize service
        service = BatchProductionService()

        # Get batches to update
        if batch_id:
            batches = Batch.objects.filter(id=batch_id)
        elif factory_id:
            batches = Batch.objects.filter(factory_id=factory_id)
        else:
            # Default: update active batches
            status_list = ['approved', 'in_process', 'paused']
            if status_filter:
                status_list = [status_filter]
            batches = Batch.objects.filter(status__in=status_list)

        if not batches.exists():
            self.stdout.write(self.style.WARNING('No batches found to update'))
            return

        self.stdout.write(f"Found {batches.count()} batches to update")
        
        if dry_run:
            self.stdout.write("DRY RUN - Analyzing batches...")
            for batch in batches:
                progress_data = service.calculate_batch_progress(batch)
                self.stdout.write(
                    f"Batch {batch.batch_number}: "
                    f"Progress {progress_data['progress_percentage']:.1f}%, "
                    f"Output {progress_data['actual_flour_output']:.2f} tons, "
                    f"Data source: {progress_data['data_source']}"
                )
            return

        # Update all batches
        results = service.update_all_batches(dry_run=False)

        # Display results
        self.stdout.write("\n" + "="*60)
        self.stdout.write("BATCH UPDATE RESULTS:")
        self.stdout.write(f"Total batches processed: {results['total']}")
        self.stdout.write(f"Successfully updated: {results['updated']}")
        self.stdout.write(f"Errors: {results['errors']}")
        
        if results['errors'] > 0:
            self.stdout.write("\nERROR DETAILS:")
            for detail in results['details']:
                if not detail['result']['success']:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  {detail['batch_number']}: {detail['result'].get('error', 'Unknown error')}"
                        )
                    )
        
        if results['updated'] > 0:
            self.stdout.write("\nSUCCESSFUL UPDATES:")
            for detail in results['details']:
                if detail['result']['success']:
                    data = detail['result']['data']
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  {detail['batch_number']}: "
                            f"Progress {data['progress_percentage']:.1f}%, "
                            f"Output {data['actual_flour_output']:.2f} tons"
                        )
                    )

        self.stdout.write("\n" + "="*60)
        self.stdout.write("Update completed!") 