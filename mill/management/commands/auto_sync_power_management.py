from django.core.management.base import BaseCommand
from mill.services.counter_sync_service import CounterSyncService
from mill.services.power_management_service import PowerManagementService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically sync data from counter database and update power management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-only',
            action='store_true',
            help='Only sync data, do not update power status',
        )
        parser.add_argument(
            '--power-only',
            action='store_true',
            help='Only update power status, do not sync data',
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Process specific device ID only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting automatic power management sync...'))
        
        sync_service = CounterSyncService()
        power_service = PowerManagementService()
        
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
        
        # Step 1: Sync data from counter database
        if not options['power_only']:
            self.stdout.write('Step 1: Syncing data from counter database...')
            if not options['dry_run']:
                synced_count = sync_service.sync_latest_data(device_id=options['device_id'])
                self.stdout.write(f'  Synced {synced_count} records from counter database')
            else:
                self.stdout.write('  Would sync latest data from counter database')
        
        # Step 2: Update power status
        if not options['sync_only']:
            self.stdout.write('Step 2: Updating power status...')
            if not options['dry_run']:
                if options['device_id']:
                    # Update specific device
                    from mill.models import Device
                    try:
                        device = Device.objects.get(id=options['device_id'])
                        updated_count = power_service.update_power_status_from_database(device=device)
                        self.stdout.write(f'  Updated power status for device {device.name}')
                    except Device.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'  Device {options["device_id"]} not found'))
                        return
                else:
                    # Update all devices
                    updated_count = power_service.update_power_status_from_database()
                    self.stdout.write(f'  Updated power status for {updated_count} devices')
            else:
                self.stdout.write('  Would update power status for all devices')
        
        # Step 3: Get summary
        if not options['dry_run']:
            self.stdout.write('Step 3: Generating summary...')
            summary = power_service.get_power_events_summary()
            
            self.stdout.write(f'Power Management Summary:')
            self.stdout.write(f'  Total devices: {summary["total_devices"]}')
            self.stdout.write(f'  Devices with power: {summary["devices_with_power"]}')
            self.stdout.write(f'  Devices without power: {summary["devices_without_power"]}')
            self.stdout.write(f'  Total power events: {summary["total_events"]}')
            self.stdout.write(f'  Unresolved events: {summary["unresolved_events"]}')
            self.stdout.write(f'  Critical events: {summary["critical_events"]}')
            
            # Calculate uptime percentage
            if summary["total_devices"] > 0:
                uptime_percentage = (summary["devices_with_power"] / summary["total_devices"]) * 100
                self.stdout.write(f'  System uptime: {uptime_percentage:.1f}%')
        
        self.stdout.write(self.style.SUCCESS('Automatic power management sync completed!')) 