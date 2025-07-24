from django.core.management.base import BaseCommand
from django.utils import timezone
from mill.services.unified_power_management_service import UnifiedPowerManagementService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Unified Power Management System - Update power status, events, and analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['update', 'summary', 'analytics', 'cleanup', 'all'],
            default='all',
            help='Action to perform'
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Specific device ID to process'
        )
        parser.add_argument(
            '--factory-id',
            type=int,
            help='Factory ID to process'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for analytics (default: 30)'
        )
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=90,
            help='Days threshold for cleanup (default: 90)'
        )

    def handle(self, *args, **options):
        action = options['action']
        device_id = options['device_id']
        factory_id = options['factory_id']
        days = options['days']
        cleanup_days = options['cleanup_days']
        
        service = UnifiedPowerManagementService()
        
        self.stdout.write(self.style.SUCCESS(f"Starting Unified Power Management - Action: {action}"))
        
        if action in ['update', 'all']:
            self.update_power_status(service, device_id, factory_id)
        
        if action in ['summary', 'all']:
            self.show_power_summary(service, device_id, factory_id)
        
        if action in ['analytics', 'all']:
            self.show_power_analytics(service, factory_id, days)
        
        if action in ['cleanup', 'all']:
            self.cleanup_old_events(service, cleanup_days)
        
        self.stdout.write(self.style.SUCCESS("Unified Power Management completed successfully"))
    
    def update_power_status(self, service, device_id, factory_id):
        """Update power status for devices"""
        self.stdout.write("Updating power status from counter database...")
        
        if device_id:
            # Update specific device
            devices = Device.objects.filter(id=device_id)
            if not devices.exists():
                self.stdout.write(self.style.ERROR(f"Device with ID {device_id} not found"))
                return
            
            result = service.update_all_devices_power_status()
            self.stdout.write(f"Updated {result['updated_count']} devices")
            if result['error_count'] > 0:
                self.stdout.write(self.style.WARNING(f"Errors: {result['error_count']}"))
        else:
            # Update all devices or factory devices
            result = service.update_all_devices_power_status()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Power status update completed: "
                    f"Updated: {result['updated_count']}, "
                    f"Errors: {result['error_count']}, "
                    f"Total: {result['total_devices']}"
                )
            )
    
    def show_power_summary(self, service, device_id, factory_id):
        """Show power summary"""
        self.stdout.write("Generating power summary...")
        
        summary = service.get_device_power_summary(device_id, factory_id)
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("POWER SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total Devices: {summary['total_devices']}")
        self.stdout.write(f"Devices with Power: {summary['devices_with_power']}")
        self.stdout.write(f"Devices without Power: {summary['devices_without_power']}")
        self.stdout.write(f"Power Events Today: {summary['power_events_today']}")
        self.stdout.write(f"Unresolved Events: {summary['unresolved_events']}")
        self.stdout.write(f"Average Uptime Today: {summary['avg_uptime_today']:.1f}%")
        self.stdout.write(f"Total Power Consumption: {summary['total_power_consumption']:.2f}")
        
        if summary['devices_data']:
            self.stdout.write("\nDevice Details:")
            self.stdout.write("-" * 30)
            for device_data in summary['devices_data'][:5]:  # Show first 5 devices
                status = "🟢 ON" if device_data['has_power'] else "🔴 OFF"
                ain1_value = device_data['ain1_value'] or 0.0
                uptime = device_data['uptime_percentage'] or 0.0
                self.stdout.write(
                    f"{device_data['device_name']}: {status} "
                    f"(AIN1: {ain1_value:.2f}, "
                    f"Uptime: {uptime:.1f}%)"
                )
    
    def show_power_analytics(self, service, factory_id, days):
        """Show power analytics"""
        self.stdout.write(f"Generating power analytics for last {days} days...")
        
        analytics = service.get_power_analytics(factory_id, days)
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("POWER ANALYTICS")
        self.stdout.write("="*50)
        
        # Power Events Summary
        events = analytics['power_events']
        self.stdout.write(f"Total Events: {events['total_events']}")
        self.stdout.write(f"Unresolved Events: {events['unresolved_events']}")
        self.stdout.write(f"Power Loss Events: {events['power_loss_events']}")
        self.stdout.write(f"Power Restored Events: {events['power_restored_events']}")
        self.stdout.write(f"Critical Events: {events['critical_events']}")
        self.stdout.write(f"High Severity Events: {events['high_severity_events']}")
        
        # Trends
        trends = analytics['trends']
        if trends:
            self.stdout.write(f"\nTrends:")
            self.stdout.write(f"Average Power Consumption: {trends['avg_power_consumption']:.2f}")
            self.stdout.write(f"Max Power Consumption: {trends['max_power_consumption']:.2f}")
            self.stdout.write(f"Total Power Losses: {trends['total_power_losses']}")
            self.stdout.write(f"Total Power Restores: {trends['total_power_restores']}")
        
        # Top Issues
        if analytics['top_issues']:
            self.stdout.write(f"\nTop Issues:")
            for issue in analytics['top_issues']:
                self.stdout.write(
                    f"- {issue['device_name']}: "
                    f"{issue['power_losses_today']} losses today, "
                    f"Uptime: {issue['uptime_percentage']:.1f}%"
                )
        
        # Recommendations
        if analytics['recommendations']:
            self.stdout.write(f"\nRecommendations:")
            for rec in analytics['recommendations']:
                icon = "🔴" if rec['type'] == 'urgent' else "🟡" if rec['type'] == 'warning' else "🔵"
                self.stdout.write(f"{icon} {rec['message']}")
    
    def cleanup_old_events(self, service, cleanup_days):
        """Clean up old power events"""
        self.stdout.write(f"Cleaning up power events older than {cleanup_days} days...")
        
        count = service.cleanup_old_power_events(cleanup_days)
        self.stdout.write(
            self.style.SUCCESS(f"Cleaned up {count} old power events")
        ) 