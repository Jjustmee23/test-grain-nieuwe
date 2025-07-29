from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.models import Batch, Factory, City, BatchTemplate
from mill.views.batch_import_views import validate_excel_data, process_batch_row
import pandas as pd
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test batch import functionality with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Test with specific factory ID',
        )
        parser.add_argument(
            '--city-id',
            type=int,
            help='Test with specific city ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without creating batches',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting batch import test...')
        )

        # Create sample Excel data
        sample_data = self.create_sample_data()
        
        # Convert to DataFrame
        df = pd.DataFrame(sample_data)
        
        try:
            # Validate data
            self.stdout.write('Validating Excel data...')
            df = validate_excel_data(df)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Data validation passed. {len(df)} rows processed.')
            )
            
            # Show sample data
            self.stdout.write('\nSample data:')
            self.stdout.write(df.head().to_string())
            
            # Process each row
            self.stdout.write('\nProcessing rows...')
            created_count = 0
            updated_count = 0
            
            for index, row in df.iterrows():
                self.stdout.write(f'\nProcessing row {index + 1}: {row["mill_name"]}')
                
                # Get factory
                factory = self.get_test_factory(row, options)
                if not factory:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ No factory found for: {row["mill_name"]}')
                    )
                    continue
                
                self.stdout.write(f'  → Factory: {factory.name}')
                
                if not options['dry_run']:
                    # Process the row
                    result = process_batch_row(
                        row, 
                        'single', 
                        None, 
                        factory.id, 
                        None, 
                        timezone.now().date().isoformat()
                    )
                    
                    if result['created']:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Created batch: {result.get("batch_number", "N/A")}')
                        )
                    elif result['updated']:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  ↻ Updated existing batch')
                        )
                    elif result['error']:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error: {result["error"]}')
                        )
                else:
                    # Dry run - just show what would happen
                    batch_number = f"{factory.name}_{timezone.now().date().strftime('%Y%m%d')}_{index + 1:03d}"
                    self.stdout.write(
                        self.style.SUCCESS(f'  → Would create batch: {batch_number}')
                    )
                    created_count += 1
            
            # Summary
            self.stdout.write('\n' + '='*50)
            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f'DRY RUN SUMMARY: Would create {created_count} batches')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'IMPORT SUMMARY: Created {created_count}, Updated {updated_count}')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during test: {str(e)}')
            )
            logger.error(f"Batch import test error: {str(e)}")

    def create_sample_data(self):
        """Create sample Excel data based on the documents provided"""
        return [
            {
                'mill_name': 'Buri Mill',
                'capacity': 400,
                'net_grains': 2853,
                'date': '2025-03-23',
                'batch_number': 'BURI_20250323_001'
            },
            {
                'mill_name': 'Mosul Mill',
                'capacity': 300,
                'net_grains': 1544,
                'date': '2025-03-23',
                'batch_number': 'MOSUL_20250323_001'
            },
            {
                'mill_name': 'Al-Hasad Mill',
                'capacity': 250,
                'net_grains': 1207,
                'date': '2025-03-23',
                'batch_number': 'HASAD_20250323_001'
            },
            {
                'mill_name': 'Al-Jazeera Mill',
                'capacity': 200,
                'net_grains': 1025,
                'date': '2025-03-23',
                'batch_number': 'JAZEERA_20250323_001'
            },
            {
                'mill_name': 'Sinjar Mill',
                'capacity': 150,
                'net_grains': 772,
                'date': '2025-03-23',
                'batch_number': 'SINJAR_20250323_001'
            },
            {
                'mill_name': 'Al-Ba\'aj Mill',
                'capacity': 125,
                'net_grains': 570,
                'date': '2025-03-23',
                'batch_number': 'BAAJ_20250323_001'
            },
            {
                'mill_name': 'Tal Afar Mill',
                'capacity': 100,
                'net_grains': 2205,
                'date': '2025-03-23',
                'batch_number': 'TALAFAR_20250323_001'
            },
            {
                'mill_name': 'Bar Al-Mansour Mill',
                'capacity': 50,
                'net_grains': 2606,
                'date': '2025-03-23',
                'batch_number': 'BARMANSOUR_20250323_001'
            }
        ]

    def get_test_factory(self, row, options):
        """Get factory for testing"""
        if options['factory_id']:
            try:
                return Factory.objects.get(id=options['factory_id'])
            except Factory.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Factory with ID {options["factory_id"]} not found')
                )
                return None
        
        if options['city_id']:
            # Find factory by name in the specified city
            return Factory.objects.filter(
                name__icontains=row['mill_name'],
                city_id=options['city_id'],
                status=True
            ).first()
        
        # Auto-detect by name
        return Factory.objects.filter(
            name__icontains=row['mill_name'],
            status=True
        ).first() 