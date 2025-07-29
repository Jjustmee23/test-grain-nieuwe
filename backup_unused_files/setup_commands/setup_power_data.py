from django.core.management.base import BaseCommand
from mill.models import Device, PowerData
from django.utils import timezone


class Command(BaseCommand):
    help = 'Initialize PowerData records for all devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing PowerData records',
        )

    def handle(self, *args, **options):
        devices = Device.objects.all()
        created_count = 0
        updated_count = 0
        
        self.stdout.write(f"Found {devices.count()} devices")
        
        for device in devices:
            power_data, created = PowerData.objects.get_or_create(
                device=device,
                defaults={
                    'has_power': True,
                    'power_threshold': 0.0,
                    'power_loss_count_today': 0,
                    'power_restore_count_today': 0,
                    'power_loss_count_week': 0,
                    'power_restore_count_week': 0,
                    'power_loss_count_month': 0,
                    'power_restore_count_month': 0,
                    'power_loss_count_year': 0,
                    'power_restore_count_year': 0,
                    'avg_power_consumption_today': 0.0,
                    'peak_power_consumption_today': 0.0,
                    'total_power_consumption_today': 0.0,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created PowerData for device: {device.name}")
            else:
                if options['force']:
                    # Reset all counters and data
                    power_data.power_loss_count_today = 0
                    power_data.power_restore_count_today = 0
                    power_data.power_loss_count_week = 0
                    power_data.power_restore_count_week = 0
                    power_data.power_loss_count_month = 0
                    power_data.power_restore_count_month = 0
                    power_data.power_loss_count_year = 0
                    power_data.power_restore_count_year = 0
                    power_data.avg_power_consumption_today = 0.0
                    power_data.peak_power_consumption_today = 0.0
                    power_data.total_power_consumption_today = 0.0
                    power_data.has_power = True
                    power_data.save()
                    updated_count += 1
                    self.stdout.write(f"Updated PowerData for device: {device.name}")
                else:
                    self.stdout.write(f"PowerData already exists for device: {device.name}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {devices.count()} devices. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        ) 