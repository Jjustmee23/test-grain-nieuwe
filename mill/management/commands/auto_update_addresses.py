from django.core.management.base import BaseCommand
from mill.models import Factory
import requests
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically update factory addresses using geocoding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of factories to process (default: 50)'
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
                self.stdout.write(f'Processing: {factory.name} in {factory.city.name if factory.city else "Unknown City"}')
                
                # Create search query
                search_query = f"{factory.name}, {factory.city.name if factory.city else 'Iraq'}"
                
                # Try to geocode using a free service
                geocode_result = self.geocode_address(search_query)
                
                if geocode_result:
                    address, lat, lng = geocode_result
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(f'[DRY RUN] Would update {factory.name}:')
                        )
                        self.stdout.write(f'  Address: {address}')
                        self.stdout.write(f'  Lat: {lat}, Lng: {lng}')
                    else:
                        factory.address = address
                        factory.latitude = lat
                        factory.longitude = lng
                        factory.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated {factory.name}:')
                        )
                        self.stdout.write(f'  Address: {address}')
                        self.stdout.write(f'  Lat: {lat}, Lng: {lng}')
                    
                    updated_count += 1
                else:
                    # Fallback: create a simple address based on city
                    fallback_address = self.create_fallback_address(factory)
                    if fallback_address:
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(f'[DRY RUN] Would add fallback address for {factory.name}: {fallback_address}')
                            )
                        else:
                            factory.address = fallback_address
                            factory.save()
                            self.stdout.write(
                                self.style.WARNING(f'Added fallback address for {factory.name}: {fallback_address}')
                            )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Could not find address for: {factory.name}')
                        )
                        error_count += 1

                # Rate limiting
                time.sleep(1)

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

    def geocode_address(self, address):
        """
        Try to geocode using a free service (Nominatim)
        Returns (formatted_address, latitude, longitude) or None if not found
        """
        try:
            # Use Nominatim (OpenStreetMap) - free service
            url = 'https://nominatim.openstreetmap.org/search'
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'iq'  # Limit to Iraq
            }
            
            headers = {
                'User-Agent': 'MillApplication/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                result = data[0]
                formatted_address = result.get('display_name', address)
                lat = float(result.get('lat', 0))
                lng = float(result.get('lon', 0))
                
                return (formatted_address, lat, lng)
            else:
                return None
                
        except requests.RequestException as e:
            logger.warning(f"Geocoding request failed for '{address}': {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"Geocoding failed for '{address}': {str(e)}")
            return None

    def create_fallback_address(self, factory):
        """
        Create a fallback address based on factory name and city
        """
        if not factory.city:
            return None
            
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