from django.core.management.base import BaseCommand
from mill.models import Factory

class Command(BaseCommand):
    help = 'List all factories and their address information'

    def handle(self, *args, **options):
        factories = Factory.objects.all().order_by('city__name', 'name')
        
        if not factories.exists():
            self.stdout.write(self.style.WARNING('No factories found.'))
            return

        self.stdout.write('=' * 80)
        self.stdout.write('FACTORY LIST')
        self.stdout.write('=' * 80)
        
        current_city = None
        for factory in factories:
            # Print city header if it's a new city
            if factory.city and factory.city.name != current_city:
                current_city = factory.city.name
                self.stdout.write(f'\n{self.style.SUCCESS(current_city.upper())}')
                self.stdout.write('-' * len(current_city))
            
            # Print factory info
            self.stdout.write(f'\nID: {factory.id}')
            self.stdout.write(f'Name: {factory.name}')
            self.stdout.write(f'City: {factory.city.name if factory.city else "No city"}')
            self.stdout.write(f'Address: {factory.address or "Not set"}')
            self.stdout.write(f'Coordinates: {factory.latitude}, {factory.longitude}' if factory.latitude and factory.longitude else 'Coordinates: Not set')
            self.stdout.write(f'Status: {"Active" if factory.status else "Inactive"}')
            self.stdout.write(f'Group: {factory.group}')
        
        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('SUMMARY')
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total factories: {factories.count()}')
        self.stdout.write(f'With address: {factories.exclude(address__isnull=True).exclude(address="").count()}')
        self.stdout.write(f'With coordinates: {factories.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()}')
        self.stdout.write(f'Active: {factories.filter(status=True).count()}')
        self.stdout.write(f'Inactive: {factories.filter(status=False).count()}') 