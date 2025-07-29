from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Batch, RawData, Device, Factory


class Command(BaseCommand):
    help = 'Check batch data situation and show which batches can/cannot be updated'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-id',
            type=int,
            help='Check specific batch by ID',
        )

    def handle(self, *args, **options):
        batch_id = options.get('batch_id')
        
        if batch_id:
            batches = Batch.objects.filter(id=batch_id)
        else:
            batches = Batch.objects.all()
        
        if not batches.exists():
            self.stdout.write(self.style.WARNING('No batches found.'))
            return
        
        self.stdout.write(f'Checking {batches.count()} batches...\n')
        
        for batch in batches:
            self.stdout.write(f'Batch: {batch.batch_number} (ID: {batch.id})')
            self.stdout.write(f'  Status: {batch.get_status_display()}')
            self.stdout.write(f'  Factory: {batch.factory.name if batch.factory else "None"}')
            
            if not batch.factory:
                self.stdout.write(self.style.ERROR('  ❌ No factory assigned'))
                continue
            
            device = batch.factory.devices.first()
            if not device:
                self.stdout.write(self.style.ERROR(f'  ❌ No device found for factory {batch.factory.name}'))
                continue
            
            self.stdout.write(f'  Device: {device.name} (ID: {device.id})')
            self.stdout.write(f'  Selected Counter: {device.selected_counter}')
            
            # Check RawData
            raw_data_count = RawData.objects.filter(device=device).count()
            latest_raw_data = RawData.objects.filter(device=device).order_by('-timestamp').first()
            
            self.stdout.write(f'  RawData records: {raw_data_count}')
            
            if latest_raw_data:
                counter_field = device.selected_counter or 'counter_2'
                counter_value = getattr(latest_raw_data, counter_field, 0)
                self.stdout.write(f'  Latest {counter_field}: {counter_value} (at {latest_raw_data.timestamp})')
                
                if batch.is_finalized:
                    self.stdout.write(self.style.WARNING('  ⚠️  Batch is finalized - cannot be updated'))
                else:
                    self.stdout.write(self.style.SUCCESS('  ✅ Can be updated'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ No RawData found for device'))
            
            self.stdout.write('')  # Empty line for readability 