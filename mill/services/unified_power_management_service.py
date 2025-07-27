import logging
from django.utils import timezone
from datetime import datetime, timedelta
from mill.models import Device, PowerEvent, DevicePowerStatus, Factory
from mill.services.power_management_service import PowerManagementService

logger = logging.getLogger(__name__)


class UnifiedPowerManagementService:
    """
    Unified service for power management operations
    """
    
    def __init__(self):
        self.power_service = PowerManagementService()
    
    def get_device_power_summary(self, factory_id=None):
        """
        Get power summary for devices, optionally filtered by factory
        """
        try:
            # Use the existing power management service
            summary = self.power_service.get_device_power_summary()
            
            # Filter by factory if specified
            if factory_id:
                devices_data = summary.get('devices_data', [])
                filtered_devices = [
                    device for device in devices_data 
                    if device.get('factory_id') == factory_id
                ]
                summary['devices_data'] = filtered_devices
                summary['total_devices'] = len(filtered_devices)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting device power summary: {str(e)}")
            return {
                'total_devices': 0,
                'online_devices': 0,
                'offline_devices': 0,
                'devices_data': [],
                'error': str(e)
            }
    
    def get_power_events_summary(self, factory_id=None, days=30):
        """
        Get power events summary, optionally filtered by factory
        """
        try:
            # Use the existing power management service
            summary = self.power_service.get_power_events_summary(days=days)
            
            # Filter by factory if specified
            if factory_id:
                events = PowerEvent.objects.filter(
                    device__factory_id=factory_id,
                    created_at__gte=timezone.now() - timedelta(days=days)
                )
                summary['total_events'] = events.count()
                summary['resolved_events'] = events.filter(is_resolved=True).count()
                summary['unresolved_events'] = events.filter(is_resolved=False).count()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting power events summary: {str(e)}")
            return {
                'total_events': 0,
                'resolved_events': 0,
                'unresolved_events': 0,
                'error': str(e)
            }
    
    def get_recent_power_events(self, factory_id=None, limit=10):
        """
        Get recent power events, optionally filtered by factory
        """
        try:
            events = PowerEvent.objects.all().order_by('-created_at')[:limit]
            
            # Filter by factory if specified
            if factory_id:
                events = events.filter(device__factory_id=factory_id)
            
            return list(events.values(
                'id', 'device__name', 'event_type', 'severity', 
                'description', 'created_at', 'is_resolved'
            ))
            
        except Exception as e:
            logger.error(f"Error getting recent power events: {str(e)}")
            return []
    
    def update_all_devices_power_status(self):
        """
        Update power status for all devices
        """
        try:
            # Use the existing power management service
            return self.power_service.update_all_devices_power_status()
            
        except Exception as e:
            logger.error(f"Error updating devices power status: {str(e)}")
            return {
                'updated_count': 0,
                'error_count': 1,
                'errors': [str(e)]
            }
    
    def get_power_analytics(self, factory_id=None, days=30):
        """
        Get power analytics, optionally filtered by factory
        """
        try:
            # Use the existing power management service
            analytics = self.power_service.get_power_analytics(days=days)
            
            # Filter by factory if specified
            if factory_id:
                # This would need to be implemented based on your analytics structure
                pass
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting power analytics: {str(e)}")
            return {
                'daily_usage': [],
                'peak_hours': [],
                'efficiency_score': 0,
                'error': str(e)
            } 