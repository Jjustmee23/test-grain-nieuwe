from django.core.management.base import BaseCommand
from mill.models import Device, DevicePowerStatus, RawData
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Test the entire power management system'

    def handle(self, *args, **options):
        self.stdout.write('=== POWER MANAGEMENT SYSTEM TEST ===\n')
        
        # 1. Check database counts
        self.stdout.write('1. DATABASE COUNTS:')
        total_devices = Device.objects.count()
        total_power_status = DevicePowerStatus.objects.count()
        total_raw_data = RawData.objects.count()
        
        self.stdout.write(f'   Total devices: {total_devices}')
        self.stdout.write(f'   Total DevicePowerStatus records: {total_power_status}')
        self.stdout.write(f'   Total RawData records: {total_raw_data}')
        
        if total_devices != total_power_status:
            self.stdout.write(self.style.WARNING(f'   ⚠️  MISMATCH: {total_devices - total_power_status} devices missing power status'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ All devices have power status records'))
        
        # 2. Check latest data
        self.stdout.write('\n2. LATEST DATA:')
        latest_raw = RawData.objects.order_by('-timestamp').first()
        if latest_raw:
            self.stdout.write(f'   Latest RawData: {latest_raw.timestamp}')
            self.stdout.write(f'   Device: {latest_raw.device.name}')
            self.stdout.write(f'   AIN1 value: {latest_raw.ain1_value}')
        else:
            self.stdout.write(self.style.ERROR('   ❌ No RawData found'))
        
        # 3. Check specific device
        self.stdout.write('\n3. SPECIFIC DEVICE CHECK (جنة_الحسين):')
        try:
            device = Device.objects.get(name='جنة_الحسين')
            power_status = DevicePowerStatus.objects.filter(device=device).first()
            
            if power_status:
                self.stdout.write(f'   Device: {device.name}')
                self.stdout.write(f'   Power status exists: ✅')
                self.stdout.write(f'   Last check: {power_status.last_power_check}')
                self.stdout.write(f'   Has power: {power_status.has_power}')
                self.stdout.write(f'   AIN1 value: {power_status.ain1_value}')
                
                # Check if last_power_check is recent
                if power_status.last_power_check:
                    time_diff = timezone.now() - power_status.last_power_check
                    if time_diff < timedelta(minutes=10):
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Last check is recent ({time_diff.seconds//60} minutes ago)'))
                    else:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Last check is old ({time_diff.days} days ago)'))
                else:
                    self.stdout.write(self.style.ERROR('   ❌ No last_power_check timestamp'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ No power status for device {device.name}'))
        except Device.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ❌ Device جنة_الحسين not found'))
        
        # 4. Check power status distribution
        self.stdout.write('\n4. POWER STATUS DISTRIBUTION:')
        with_power = DevicePowerStatus.objects.filter(has_power=True).count()
        without_power = DevicePowerStatus.objects.filter(has_power=False).count()
        no_status = total_devices - total_power_status
        
        self.stdout.write(f'   Devices with power: {with_power}')
        self.stdout.write(f'   Devices without power: {without_power}')
        self.stdout.write(f'   Devices without status: {no_status}')
        
        # 5. Check recent updates
        self.stdout.write('\n5. RECENT UPDATES:')
        recent_updates = DevicePowerStatus.objects.filter(
            last_power_check__gte=timezone.now() - timedelta(hours=1)
        ).count()
        self.stdout.write(f'   Updated in last hour: {recent_updates}')
        
        # 6. Test manual update
        self.stdout.write('\n6. MANUAL UPDATE TEST:')
        try:
            device = Device.objects.get(name='جنة_الحسين')
            latest_raw = RawData.objects.filter(
                device=device,
                ain1_value__isnull=False
            ).order_by('-timestamp').first()
            
            if latest_raw:
                power_status, created = DevicePowerStatus.objects.get_or_create(
                    device=device,
                    defaults={'power_threshold': 0.0}
                )
                
                old_check = power_status.last_power_check
                power_status.ain1_value = latest_raw.ain1_value
                power_status.last_power_check = latest_raw.timestamp or timezone.now()
                power_status.has_power = latest_raw.ain1_value > 0
                power_status.save()
                
                self.stdout.write(f'   ✅ Manual update successful')
                self.stdout.write(f'   Old check: {old_check}')
                self.stdout.write(f'   New check: {power_status.last_power_check}')
                self.stdout.write(f'   AIN1: {power_status.ain1_value}')
                self.stdout.write(f'   Has power: {power_status.has_power}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ No RawData for manual update test'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Manual update failed: {str(e)}'))
        
        self.stdout.write('\n=== TEST COMPLETED ===') 