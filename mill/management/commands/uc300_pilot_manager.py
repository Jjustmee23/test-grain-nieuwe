"""
🔄 UC300 Pilot Manager - Django Management Command
Command-line interface for managing the UC300 reset pilot system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from mill.models import Device, CounterResetLog, UC300PilotStatus
from mill.services.uc300_command_service import UC300CommandService, reset_device_counter
from mill.services.uc300_production_service import UC300ProductionService


class Command(BaseCommand):
    help = '🔄 Manage UC300 Reset Pilot System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['status', 'enable', 'disable', 'reset', 'test', 'update'],
            required=True,
            help='Action to perform'
        )
        
        parser.add_argument(
            '--device-id',
            type=str,
            help='Device ID for device-specific actions'
        )
        
        parser.add_argument(
            '--reset-time',
            type=str,
            default='06:00',
            help='Daily reset time (HH:MM format, default: 06:00)'
        )
        
        parser.add_argument(
            '--counter',
            type=int,
            default=2,
            help='Counter number to reset (1-4, default: 2)'
        )
        
        parser.add_argument(
            '--reason',
            type=str,
            default='manual',
            choices=['manual', 'daily', 'batch_start', 'maintenance'],
            help='Reason for reset'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (no actual changes)'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔄 DRY RUN MODE - No actual changes will be made'))
        
        action = options['action']
        
        try:
            if action == 'status':
                self.show_pilot_status()
            elif action == 'enable':
                self.enable_pilot(options)
            elif action == 'disable':
                self.disable_pilot(options)
            elif action == 'reset':
                self.reset_device(options)
            elif action == 'test':
                self.test_pilot_system(options)
            elif action == 'update':
                self.update_production(options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise CommandError(str(e))

    def show_pilot_status(self):
        """Show current pilot status"""
        self.stdout.write(self.style.SUCCESS('🔄 UC300 RESET PILOT STATUS'))
        self.stdout.write('=' * 60)
        
        service = UC300ProductionService()
        summary = service.get_pilot_status_summary()
        
        if 'error' in summary:
            self.stdout.write(self.style.ERROR(f'Error getting status: {summary["error"]}'))
            return
        
        # Overall statistics
        self.stdout.write(f"\n📊 OVERVIEW:")
        self.stdout.write(f"  Total Devices: {summary['total_devices']}")
        self.stdout.write(f"  Pilot Devices: {summary['pilot_devices']}")
        self.stdout.write(f"  Non-Pilot Devices: {summary['non_pilot_devices']}")
        self.stdout.write(f"  Pilot Coverage: {summary['pilot_percentage']}%")
        
        # Pilot devices details
        if summary['pilot_devices_list']:
            self.stdout.write(f"\n🎯 PILOT DEVICES:")
            self.stdout.write("-" * 40)
            
            for device in summary['pilot_devices_list']:
                status_icon = "🟢" if device['use_reset_logic'] else "🟡"
                self.stdout.write(f"  {status_icon} {device['device_name']} ({device['device_id']})")
                self.stdout.write(f"     Reset Time: {device['daily_reset_time'] or 'Not set'}")
                self.stdout.write(f"     Days in Pilot: {device['days_in_pilot']}")
                self.stdout.write(f"     Reset Logic: {'Enabled' if device['use_reset_logic'] else 'Disabled'}")
                self.stdout.write("")
        
        # Recent reset activity
        self.show_recent_resets()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Status report completed'))

    def show_recent_resets(self):
        """Show recent reset activity"""
        try:
            recent_resets = CounterResetLog.objects.filter(
                reset_timestamp__gte=timezone.now() - timezone.timedelta(days=7)
            ).select_related('device').order_by('-reset_timestamp')[:10]
            
            if recent_resets:
                self.stdout.write(f"\n🔄 RECENT RESETS (Last 7 days):")
                self.stdout.write("-" * 40)
                
                for reset in recent_resets:
                    status_icon = "✅" if reset.reset_successful else "❌"
                    reason_icons = {
                        'daily': '⏰',
                        'batch_start': '🎯',
                        'manual': '👤',
                        'maintenance': '🔧'
                    }
                    reason_icon = reason_icons.get(reset.reset_reason, '🔄')
                    
                    self.stdout.write(
                        f"  {status_icon} {reset.device.name} - "
                        f"{reset.reset_timestamp.strftime('%Y-%m-%d %H:%M')} - "
                        f"{reason_icon} {reset.get_reset_reason_display()}"
                    )
            else:
                self.stdout.write(f"\n🔄 No recent resets found")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting recent resets: {str(e)}'))

    def enable_pilot(self, options):
        """Enable pilot for a device"""
        device_id = options.get('device_id')
        if not device_id:
            raise CommandError("--device-id is required for enable action")
        
        reset_time = options.get('reset_time', '06:00')
        
        self.stdout.write(f"🔄 Enabling UC300 pilot for device: {device_id}")
        self.stdout.write(f"   Reset time: {reset_time}")
        
        if not self.dry_run:
            service = UC300ProductionService()
            success = service.enable_device_pilot(
                device_id, 
                reset_time, 
                f"Enabled via management command at {timezone.now()}"
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ Pilot enabled for device {device_id}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to enable pilot for device {device_id}'))
        else:
            self.stdout.write(self.style.WARNING('🔄 DRY RUN: Would enable pilot'))

    def disable_pilot(self, options):
        """Disable pilot for a device"""
        device_id = options.get('device_id')
        if not device_id:
            raise CommandError("--device-id is required for disable action")
        
        self.stdout.write(f"🔄 Disabling UC300 pilot for device: {device_id}")
        
        if not self.dry_run:
            service = UC300ProductionService()
            success = service.disable_device_pilot(device_id)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ Pilot disabled for device {device_id}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to disable pilot for device {device_id}'))
        else:
            self.stdout.write(self.style.WARNING('🔄 DRY RUN: Would disable pilot'))

    def reset_device(self, options):
        """Reset a device counter"""
        device_id = options.get('device_id')
        if not device_id:
            raise CommandError("--device-id is required for reset action")
        
        counter = options.get('counter', 2)
        reason = options.get('reason', 'manual')
        
        self.stdout.write(f"🔄 Resetting device: {device_id}")
        self.stdout.write(f"   Counter: {counter}")
        self.stdout.write(f"   Reason: {reason}")
        
        if not self.dry_run:
            self.stdout.write("⚠️  Sending reset command to UC300 device...")
            
            success = reset_device_counter(device_id, counter, reason)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ Reset command successful for device {device_id}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Reset command failed for device {device_id}'))
        else:
            self.stdout.write(self.style.WARNING('🔄 DRY RUN: Would send reset command'))

    def test_pilot_system(self, options):
        """Test the pilot system"""
        device_id = options.get('device_id')
        
        self.stdout.write(self.style.SUCCESS('🧪 TESTING UC300 PILOT SYSTEM'))
        self.stdout.write('=' * 60)
        
        # Test 1: MQTT connection
        self.stdout.write("\n🔌 Testing MQTT connection...")
        try:
            with UC300CommandService() as service:
                if service.is_connected:
                    self.stdout.write(self.style.SUCCESS('✅ MQTT connection successful'))
                else:
                    self.stdout.write(self.style.ERROR('❌ MQTT connection failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ MQTT connection error: {str(e)}'))
        
        # Test 2: Database models
        self.stdout.write("\n🗄️ Testing database models...")
        try:
            pilot_count = UC300PilotStatus.objects.count()
            reset_count = CounterResetLog.objects.count()
            self.stdout.write(self.style.SUCCESS(f'✅ Database models working'))
            self.stdout.write(f'   Pilot statuses: {pilot_count}')
            self.stdout.write(f'   Reset logs: {reset_count}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database model error: {str(e)}'))
        
        # Test 3: Production service
        self.stdout.write("\n⚙️ Testing production service...")
        try:
            service = UC300ProductionService()
            summary = service.get_pilot_status_summary()
            if 'error' not in summary:
                self.stdout.write(self.style.SUCCESS('✅ Production service working'))
                self.stdout.write(f'   Pilot devices: {summary["pilot_devices"]}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Production service error: {summary["error"]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Production service error: {str(e)}'))
        
        # Test 4: Device-specific test
        if device_id:
            self.stdout.write(f"\n🎯 Testing device: {device_id}")
            try:
                device = Device.objects.filter(id=device_id).first()
                if device:
                    service = UC300ProductionService()
                    is_pilot = service.is_device_in_pilot(device_id)
                    
                    self.stdout.write(self.style.SUCCESS(f'✅ Device found: {device.name}'))
                    self.stdout.write(f'   Pilot status: {"🟢 ACTIVE" if is_pilot else "⚪ INACTIVE"}')
                    
                    if is_pilot:
                        reset_today = service.get_reset_log_today(device_id)
                        self.stdout.write(f'   Reset today: {"Yes" if reset_today else "No"}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Device {device_id} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Device test error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ System test completed'))

    def update_production(self, options):
        """Update production data"""
        device_id = options.get('device_id')
        
        if device_id:
            self.stdout.write(f"🔄 Updating production for device: {device_id}")
            
            if not self.dry_run:
                service = UC300ProductionService()
                result = service.update_device_production_with_reset_awareness(device_id)
                
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(f'✅ Production updated for device {device_id}'))
                    self.stdout.write(f'   Method: {result.get("calculation_method")}')
                    self.stdout.write(f'   Daily: {result.get("daily_production")}')
                    self.stdout.write(f'   Reset today: {result.get("reset_today")}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to update production: {result.get("error")}'))
            else:
                self.stdout.write(self.style.WARNING('🔄 DRY RUN: Would update production'))
        else:
            self.stdout.write("🔄 Updating production for all devices (hybrid mode)")
            
            if not self.dry_run:
                service = UC300ProductionService()
                result = service.update_all_production_data_hybrid()
                
                if result.get('success'):
                    pilot_results = result.get('pilot_results', {})
                    self.stdout.write(self.style.SUCCESS('✅ Hybrid production update completed'))
                    self.stdout.write(f'   Pilot devices updated: {pilot_results.get("devices_updated", 0)}')
                    self.stdout.write(f'   Pilot errors: {pilot_results.get("errors", 0)}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to update production: {result.get("error")}'))
            else:
                self.stdout.write(self.style.WARNING('🔄 DRY RUN: Would update all production')) 