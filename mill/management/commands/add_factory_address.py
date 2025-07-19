from django.core.management.base import BaseCommand
from mill.models import Factory

class Command(BaseCommand):
    help = 'Add or update factory addresses manually'

    def add_arguments(self, parser):
        parser.add_argument(
            '--factory-id',
            type=int,
            required=True,
            help='Factory ID to update'
        )
        parser.add_argument(
            '--address',
            type=str,
            required=True,
            help='Full address of the factory'
        )
        parser.add_argument(
            '--latitude',
            type=float,
            help='Latitude coordinate (optional)'
        )
        parser.add_argument(
            '--longitude',
            type=float,
            help='Longitude coordinate (optional)'
        )

    def handle(self, *args, **options):
        factory_id = options['factory_id']
        address = options['address']
        latitude = options.get('latitude')
        longitude = options.get('longitude')

        try:
            factory = Factory.objects.get(id=factory_id)
        except Factory.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Factory with ID {factory_id} does not exist.')
            )
            return

        # Show current info
        self.stdout.write(f'Current factory info:')
        self.stdout.write(f'  Name: {factory.name}')
        self.stdout.write(f'  City: {factory.city.name if factory.city else "No city"}')
        self.stdout.write(f'  Current address: {factory.address or "Not set"}')
        self.stdout.write(f'  Current coordinates: {factory.latitude}, {factory.longitude}' if factory.latitude and factory.longitude else 'Not set')

        # Update the factory
        factory.address = address
        if latitude is not None:
            factory.latitude = latitude
        if longitude is not None:
            factory.longitude = longitude

        factory.save()

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully updated factory {factory.name}:')
        )
        self.stdout.write(f'  New address: {factory.address}')
        self.stdout.write(f'  New coordinates: {factory.latitude}, {factory.longitude}') 