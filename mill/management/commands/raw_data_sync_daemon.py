from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import time
import logging
import signal
import sys

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Daemon to sync raw_data from mqtt_data every 5 minutes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes in seconds
            help='Sync interval in seconds (default: 300)',
        )
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Logging level (default: INFO)',
        )

    def handle(self, *args, **options):
        interval = options.get('interval')
        log_level = options.get('log_level')
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        self.stdout.write(
            self.style.SUCCESS(f'=== RAW_DATA SYNC DAEMON STARTED ===')
        )
        self.stdout.write(f'Sync interval: {interval} seconds ({interval/60:.1f} minutes)')
        self.stdout.write(f'Log level: {log_level}')
        self.stdout.write('Press Ctrl+C to stop')

        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write(
                self.style.WARNING('\n=== SHUTDOWN SIGNAL RECEIVED ===')
            )
            self.stdout.write('Stopping raw_data sync daemon...')
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        sync_count = 0
        start_time = timezone.now()

        try:
            while True:
                try:
                    current_time = timezone.now()
                    sync_count += 1
                    
                    self.stdout.write(f'\n[{current_time.strftime("%Y-%m-%d %H:%M:%S")}] Sync #{sync_count} starting...')
                    
                    # Run the sync command
                    call_command('sync_raw_data', verbosity=1)
                    
                    # Calculate next sync time
                    next_sync = current_time + timezone.timedelta(seconds=interval)
                    self.stdout.write(f'Next sync at: {next_sync.strftime("%Y-%m-%d %H:%M:%S")}')
                    
                    # Show uptime statistics
                    uptime = current_time - start_time
                    self.stdout.write(f'Uptime: {uptime.days} days, {uptime.seconds//3600} hours, {(uptime.seconds%3600)//60} minutes')
                    self.stdout.write(f'Total syncs: {sync_count}')
                    
                    # Sleep until next sync
                    self.stdout.write(f'Sleeping for {interval} seconds...')
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error during sync: {str(e)}')
                    )
                    logger.error(f'Sync error: {str(e)}', exc_info=True)
                    
                    # Wait a bit before retrying
                    self.stdout.write('Waiting 60 seconds before retry...')
                    time.sleep(60)
                    
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\n=== DAEMON STOPPED BY USER ===')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n=== DAEMON CRASHED: {str(e)} ===')
            )
            logger.error(f'Daemon crash: {str(e)}', exc_info=True)
            raise

        self.stdout.write(
            self.style.SUCCESS('=== RAW_DATA SYNC DAEMON STOPPED ===')
        ) 