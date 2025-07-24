from django.core.management.base import BaseCommand
from mill.models import Device, DoorStatus, RawData
from django.db import transaction


class Command(BaseCommand):
    help = 'Initialize door status for existing devices based on latest din data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing door status records',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        devices = Device.objects.all()
        created_count = 0
        updated_count = 0
        
        self.stdout.write(f"Processing {devices.count()} devices...")
        
        for device in devices:
            try:
                with transaction.atomic():
                    # Get latest raw data for this device
                    latest_raw_data = RawData.objects.filter(
                        device=device,
                        din__isnull=False
                    ).exclude(din='').order_by('-timestamp').first()
                    
                    if latest_raw_data and latest_raw_data.din:
                        # Parse din data to determine door status
                        try:
                            din_array = eval(latest_raw_data.din) if isinstance(latest_raw_data.din, str) else latest_raw_data.din
                            
                            if isinstance(din_array, list) and len(din_array) > 3:
                                door_value = din_array[3]  # Default to index 3 (last element)
                                is_open = door_value == 1
                                
                                # Get or create door status
                                door_status, created = DoorStatus.objects.get_or_create(
                                    device=device,
                                    defaults={
                                        'is_open': is_open,
                                        'last_din_data': latest_raw_data.din,
                                        'door_input_index': 3
                                    }
                                )
                                
                                if created:
                                    created_count += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"Created door status for {device.name}: {'Open' if is_open else 'Closed'}"
                                        )
                                    )
                                elif force:
                                    # Update existing record
                                    door_status.is_open = is_open
                                    door_status.last_din_data = latest_raw_data.din
                                    door_status.save()
                                    updated_count += 1
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"Updated door status for {device.name}: {'Open' if is_open else 'Closed'}"
                                        )
                                    )
                                else:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"Door status already exists for {device.name}, skipping (use --force to update)"
                                        )
                                    )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"Invalid din data format for {device.name}: {latest_raw_data.din}"
                                    )
                                )
                        except (ValueError, SyntaxError, TypeError) as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Error parsing din data for {device.name}: {e}"
                                )
                            )
                    else:
                        # Create default door status (closed) if no din data available
                        door_status, created = DoorStatus.objects.get_or_create(
                            device=device,
                            defaults={
                                'is_open': False,
                                'last_din_data': None,
                                'door_input_index': 3
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Created default door status for {device.name}: Closed (no din data)"
                                )
                            )
                        elif force:
                            door_status.is_open = False
                            door_status.last_din_data = None
                            door_status.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Updated door status for {device.name}: Closed (no din data)"
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Door status already exists for {device.name}, skipping (use --force to update)"
                                )
                            )
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing device {device.name}: {e}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDoor status initialization completed!\n"
                f"Created: {created_count}\n"
                f"Updated: {updated_count}\n"
                f"Total devices processed: {devices.count()}"
            )
        ) 