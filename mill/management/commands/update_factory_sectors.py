from django.core.management.base import BaseCommand
from mill.models import Factory

class Command(BaseCommand):
    help = 'Update factory sectors from "Public" to "government"'

    def handle(self, *args, **options):
        self.stdout.write('Updating factory sectors...')
        
        # Update all factories with group='Public' to group='government'
        updated_count = Factory.objects.filter(group='Public').update(group='government')
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} factories from "Public" to "government"')
            )
        else:
            self.stdout.write('No factories found with group="Public"')
        
        # Show current distribution
        self.stdout.write('\nCurrent factory sector distribution:')
        for group, _ in Factory.GROUP_CHOICES:
            count = Factory.objects.filter(group=group).count()
            self.stdout.write(f'  {group}: {count} factories') 