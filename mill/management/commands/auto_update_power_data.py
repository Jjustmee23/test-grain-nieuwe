from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.services.unified_power_management_service import UnifiedPowerManagementService
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically update power data every 5 minutes'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=300, help='Update interval in seconds (default: 300)')
        parser.add_argument('--once', action='store_true', help='Run once and exit')

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        self.stdout.write(f"Starting automatic power data updates (interval: {interval} seconds)")
        
        try:
            while True:
                start_time = timezone.now()
                
                self.stdout.write(f"\n[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Updating power data...")
                
                # Update all devices power status
                service = UnifiedPowerManagementService()
                update_result = service.update_all_devices_power_status()
                
                self.stdout.write(f"Update completed: {update_result}")
                
                if run_once:
                    self.stdout.write("Run once completed, exiting...")
                    break
                
                # Wait for next update
                self.stdout.write(f"Waiting {interval} seconds until next update...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write("\nStopping automatic updates...")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in auto_update_power_data command: {e}") 