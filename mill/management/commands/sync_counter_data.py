from django.core.management.base import BaseCommand
from mill.services.counter_sync_service import CounterSyncService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync data from counter database to testdb and update power management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=str,
            help='Sync data for specific device ID',
        )
        parser.add_argument(
            '--historical',
            action='store_true',
            help='Sync historical data (last 7 days)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days for historical sync (default: 7)',
        )
        parser.add_argument(
            '--update-power',
            action='store_true',
            help='Update power status after syncing',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting counter database sync...'))
        
        sync_service = CounterSyncService()
        
        # Check counter database status
        status = sync_service.get_counter_db_status()
        if status.get('connection_status') == 'error':
            self.stdout.write(self.style.ERROR(f'Cannot connect to counter database: {status.get("error_message")}'))
            return
        
        self.stdout.write(f'Counter database status:')
        self.stdout.write(f'  Total records: {status.get("total_records", 0)}')
        self.stdout.write(f'  Unique devices: {status.get("unique_devices", 0)}')
        self.stdout.write(f'  Recent records (24h): {status.get("recent_records_24h", 0)}')
        self.stdout.write(f'  Latest timestamp: {status.get("latest_timestamp")}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
        
        # Sync data
        if options['historical']:
            self.stdout.write(f'Syncing historical data for last {options["days"]} days...')
            if not options['dry_run']:
                synced_count = sync_service.sync_historical_data(
                    days=options['days'],
                    device_id=options['device_id']
                )
                self.stdout.write(f'Synced {synced_count} historical records')
            else:
                self.stdout.write('Would sync historical data')
        else:
            self.stdout.write('Syncing latest data...')
            if not options['dry_run']:
                synced_count = sync_service.sync_latest_data(device_id=options['device_id'])
                self.stdout.write(f'Synced {synced_count} latest records')
            else:
                self.stdout.write('Would sync latest data')
        
        # Update power status
        if options['update_power'] and not options['dry_run']:
            self.stdout.write('Updating power status...')
            updated_count = sync_service.update_power_status_from_counter_db()
            self.stdout.write(f'Updated power status for {updated_count} devices')
        elif options['update_power'] and options['dry_run']:
            self.stdout.write('Would update power status')
        
        self.stdout.write(self.style.SUCCESS('Counter database sync completed!')) 