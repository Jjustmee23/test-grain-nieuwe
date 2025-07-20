from django.core.management.base import BaseCommand
from django.conf import settings
from mill.models import Factory, City
import requests
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update factory addresses and coordinates based on factory name and city'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Google Maps API key (optional, will use settings if not provided)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Update only a specific factory by ID'
        )

    def handle(self, *args, **options):
        api_key = options['api_key'] or getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        dry_run = options['dry_run']
        factory_id = options['factory_id']

        if not api_key:
            self.stdout.write(
                self.style.ERROR('No Google Maps API key provided. Please provide --api-key or set GOOGLE_MAPS_API_KEY in settings.')
            )
            return

        # Get factories to update
        if factory_id:
            factories = Factory.objects.filter(id=factory_id)
        else:
            factories = Factory.objects.filter(address__isnull=True).exclude(address='')

        if not factories.exists():
            self.stdout.write(
                self.style.WARNING('No factories found to update.')
            )
            return

        self.stdout.write(f'Found {factories.count()} factories to update...')

        updated_count = 0
        error_count = 0

        for factory in factories:
            try:
                self.stdout.write(f'Processing: {factory.name} in {factory.city.name if factory.city else "Unknown City"}')
                
                # Create search query
                search_query = f"{factory.name}, {factory.city.name if factory.city else ''}"
                
                # Geocode the address
                geocode_result = self.geocode_address(search_query, api_key)
                
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
                    self.stdout.write(
                        self.style.WARNING(f'Could not find address for: {factory.name}')
                    )
                    error_count += 1

                # Rate limiting - be nice to the API
                time.sleep(0.5)

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

    def geocode_address(self, address, api_key):
        """
        Geocode an address using Google Maps Geocoding API
        Returns (formatted_address, latitude, longitude) or None if not found
        """
        try:
            url = 'https://maps.googleapis.com/maps/api/geocode/json'
            params = {
                'address': address,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                formatted_address = result['formatted_address']
                location = result['geometry']['location']
                
                return (
                    formatted_address,
                    location['lat'],
                    location['lng']
                )
            else:
                logger.warning(f"Geocoding failed for '{address}': {data.get('status', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request error for '{address}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for '{address}': {str(e)}")
            return None 