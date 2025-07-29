from django.core.management.base import BaseCommand
from mill.models import Device, RawData, DoorOpenLogs
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate simple door history from RawData'

    def add_arguments(self, parser):
        parser.add_argument(
            '--generate-history',
            action='store_true',
            help='Generate door history from historical RawData',
        )
        parser.add_argument(
            '--update-current',
            action='store_true',
            help='Update current door status from latest RawData',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Number of days back to process for history generation',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting door history generation...'))
        
        if options['generate_history']:
            self.generate_door_history(options)
        
        if options['update_current']:
            self.update_current_door_status(options)
        
        if not options['generate_history'] and not options['update_current']:
            self.stdout.write('Please specify --generate-history or --update-current or both')

    def generate_door_history(self, options):
        """Generate door history from historical RawData"""
        start_date = timezone.now() - timedelta(days=options['days_back'])
        
        devices = Device.objects.all()
        total_processed = 0
        
        for device in devices:
            self.stdout.write(f'Processing device: {device.name}')
            
            # Get RawData entries with DIN data
            raw_data_entries = RawData.objects.filter(
                device=device,
                din__isnull=False
            ).exclude(din='').filter(
                timestamp__gte=start_date
            ).order_by('timestamp')
            
            door_open_start = None
            door_input_index = 3  # Default door input index
            
            for entry in raw_data_entries:
                try:
                    din_data = json.loads(entry.din) if isinstance(entry.din, str) else entry.din
                    
                    if not isinstance(din_data, list) or len(din_data) <= door_input_index:
                        continue
                    
                    door_status = din_data[door_input_index]
                    
                    # Door opens (transition from 0 to 1)
                    if door_status == 1 and door_open_start is None:
                        door_open_start = entry.timestamp
                    
                    # Door closes (transition from 1 to 0)
                    elif door_status == 0 and door_open_start is not None:
                        duration = entry.timestamp - door_open_start
                        
                        # Create door open log
                        DoorOpenLogs.objects.get_or_create(
                            device=device,
                            timestamp=door_open_start,
                            defaults={
                                'din_data': entry.din,
                                'door_input_index': door_input_index,
                                'is_resolved': True,
                                'resolved_at': entry.timestamp
                            }
                        )
                        
                        door_open_start = None
                        total_processed += 1
                
                except (json.JSONDecodeError, IndexError, TypeError) as e:
                    continue
            
            # Handle case where door is still open at the end
            if door_open_start is not None:
                DoorOpenLogs.objects.get_or_create(
                    device=device,
                    timestamp=door_open_start,
                    defaults={
                        'din_data': raw_data_entries.last().din if raw_data_entries.exists() else '',
                        'door_input_index': door_input_index,
                        'is_resolved': False,
                        'resolved_at': None
                    }
                )
        
        self.stdout.write(self.style.SUCCESS(f'Generated {total_processed} door open events'))

    def update_current_door_status(self, options):
        """Update current door status from latest RawData"""
        devices = Device.objects.all()
        
        for device in devices:
            latest_raw_data = RawData.objects.filter(
                device=device,
                din__isnull=False
            ).exclude(din='').order_by('-timestamp').first()
            
            if latest_raw_data:
                try:
                    din_data = json.loads(latest_raw_data.din) if isinstance(latest_raw_data.din, str) else latest_raw_data.din
                    door_input_index = 3
                    
                    if isinstance(din_data, list) and len(din_data) > door_input_index:
                        door_status = din_data[door_input_index]
                        
                        # Check if this is a new door opening
                        if door_status == 1:
                            # Check if we already have an open log for this device
                            existing_open = DoorOpenLogs.objects.filter(
                                device=device,
                                is_resolved=False
                            ).first()
                            
                            if not existing_open:
                                # Create new door open log
                                DoorOpenLogs.objects.create(
                                    device=device,
                                    timestamp=latest_raw_data.timestamp,
                                    din_data=latest_raw_data.din,
                                    door_input_index=door_input_index,
                                    is_resolved=False,
                                    resolved_at=None
                                )
                                self.stdout.write(f'New door opening detected for {device.name}')
                        
                        elif door_status == 0:
                            # Close any open door logs
                            open_logs = DoorOpenLogs.objects.filter(
                                device=device,
                                is_resolved=False
                            )
                            
                            for open_log in open_logs:
                                open_log.is_resolved = True
                                open_log.resolved_at = latest_raw_data.timestamp
                                open_log.save()
                                duration = latest_raw_data.timestamp - open_log.timestamp
                                self.stdout.write(f'Door closed for {device.name}, duration: {duration.total_seconds() / 60:.1f} minutes')
                
                except (json.JSONDecodeError, IndexError, TypeError) as e:
                    continue 