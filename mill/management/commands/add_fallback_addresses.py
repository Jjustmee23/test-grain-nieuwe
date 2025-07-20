from django.core.management.base import BaseCommand
from mill.models import Factory

class Command(BaseCommand):
    help = 'Add fallback addresses for all factories without addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of factories to process (default: 100)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        # Get factories without addresses
        factories = Factory.objects.filter(
            address__isnull=True
        ).exclude(
            address=''
        )[:limit]

        if not factories.exists():
            self.stdout.write(
                self.style.WARNING('No factories found without addresses.')
            )
            return

        self.stdout.write(f'Found {factories.count()} factories to update...')

        updated_count = 0
        error_count = 0

        for factory in factories:
            try:
                fallback_address = self.create_fallback_address(factory)
                
                if fallback_address:
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(f'[DRY RUN] Would add address for {factory.name}: {fallback_address}')
                        )
                    else:
                        factory.address = fallback_address
                        factory.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'Added address for {factory.name}: {fallback_address}')
                        )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Could not create address for: {factory.name}')
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {factory.name}: {str(e)}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Total factories processed: {factories.count()}')
        self.stdout.write(f'Successfully updated: {updated_count}')
        self.stdout.write(f'Errors: {error_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run. No changes were made.')
            )

    def create_fallback_address(self, factory):
        """
        Create a fallback address based on factory name and city
        """
        if not factory.city:
            return f'{factory.name}, Iraq'
            
        city_name = factory.city.name.split('-')[0] if '-' in factory.city.name else factory.city.name
        
        # Simple fallback addresses based on city
        fallback_addresses = {
            'بغداد': f'{factory.name}, Baghdad, Iraq',
            'كربلاء': f'{factory.name}, Karbala, Iraq',
            'كركوك': f'{factory.name}, Kirkuk, Iraq',
            'دهوك': f'{factory.name}, Duhok, Iraq',
            'ديالى': f'{factory.name}, Diyala, Iraq',
            'ذي قار': f'{factory.name}, Dhi Qar, Iraq',
            'صلاح الدين': f'{factory.name}, Salah Aldin, Iraq',
            'ميسان': f'{factory.name}, Maysan, Iraq',
            'واسط': f'{factory.name}, Wasit, Iraq',
        }
        
        for arabic_city, address_template in fallback_addresses.items():
            if arabic_city in city_name:
                return address_template
        
        # Default fallback
        return f'{factory.name}, {city_name}, Iraq' 