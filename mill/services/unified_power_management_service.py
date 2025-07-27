from django.utils import timezone
from django.db.models import Q, Count, Avg, Max, Min
from datetime import timedelta
from mill.models import (
    Device, PowerData, PowerEvent, DevicePowerStatus, 
    PowerNotificationSettings, Notification, NotificationCategory
)
import logging

logger = logging.getLogger(__name__)


class UnifiedPowerManagementService:
    """Unified service for managing all power-related functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def update_all_devices_power_status(self):
        """Update power status for all devices from counter database"""
        devices = Device.objects.all()
        updated_count = 0
        error_count = 0
        
        for device in devices:
            try:
                power_data, created = PowerData.objects.get_or_create(
                    device=device,
                    defaults={
                        'has_power': True,
                        'power_threshold': 0.0,
                    }
                )
                
                success = power_data.update_from_counter_db()
                if success:
                    updated_count += 1
                    self.logger.info(f"Updated power status for device: {device.name}")
                else:
                    error_count += 1
                    self.logger.warning(f"Failed to update power status for device: {device.name}")
                    
            except Exception as e:
                error_count += 1
                self.logger.error(f"Error updating power status for device {device.name}: {e}")
        
        return {
            'updated_count': updated_count,
            'error_count': error_count,
            'total_devices': devices.count()
        }
    
    def get_device_power_summary(self, device_id=None, factory_id=None):
        """Get comprehensive power summary for devices"""
        devices = Device.objects.all()
        
        if device_id:
            devices = devices.filter(id=device_id)
        elif factory_id:
            devices = devices.filter(factory_id=factory_id)
        
        # If no devices found, return empty summary
        if not devices.exists():
            return {
                'total_devices': 0,
                'devices_with_power': 0,
                'devices_without_power': 0,
                'power_events_today': 0,
                'unresolved_events': 0,
                'avg_uptime_today': 0.0,
                'total_power_consumption': 0.0,
                'devices_data': []
            }
        
        summary = {
            'total_devices': devices.count(),
            'devices_with_power': 0,
            'devices_without_power': 0,
            'power_events_today': 0,
            'unresolved_events': 0,
            'avg_uptime_today': 0.0,
            'total_power_consumption': 0.0,
            'devices_data': []
        }
        
        total_uptime = 0.0
        device_count = 0
        
        for device in devices:
            power_data = PowerData.objects.filter(device=device).first()
            
            # Get latest AIN1 value from RawData if PowerData doesn't have it
            ain1_value = None
            last_update = None
            
            if power_data:
                ain1_value = power_data.ain1_value
                last_update = power_data.last_mqtt_update
            
            # If no AIN1 value in PowerData, get from RawData
            if ain1_value is None:
                from mill.models import RawData
                latest_raw_data = RawData.objects.filter(
                    device=device,
                    ain1_value__isnull=False
                ).order_by('-timestamp').first()
                
                if latest_raw_data:
                    ain1_value = latest_raw_data.ain1_value
                    last_update = latest_raw_data.timestamp
            
            # Determine power status based on AIN1 value
            has_power = False
            if ain1_value is not None:
                power_threshold = power_data.power_threshold if power_data else 0.0
                has_power = ain1_value > power_threshold
            
            device_data = {
                'device_id': device.id,
                'device_name': device.name,
                'factory_name': device.factory.name if device.factory else 'Unknown',
                'has_power': has_power,
                'ain1_value': ain1_value,
                'last_update': last_update,
                'power_loss_count_today': power_data.power_loss_count_today if power_data else 0,
                'power_restore_count_today': power_data.power_restore_count_today if power_data else 0,
                'uptime_percentage': power_data.get_uptime_percentage_today() if power_data else 100.0,
                'last_power_loss': power_data.last_power_loss if power_data else None,
                'last_power_restore': power_data.last_power_restore if power_data else None,
                'peak_consumption_today': power_data.peak_power_consumption_today if power_data else 0.0,
                'total_consumption_today': power_data.total_power_consumption_today if power_data else 0.0,
                'power_threshold': power_data.power_threshold if power_data else 0.0,
            }
            
            if has_power:
                summary['devices_with_power'] += 1
            else:
                summary['devices_without_power'] += 1
            
            uptime_percentage = power_data.get_uptime_percentage_today() if power_data else 100.0
            total_uptime += uptime_percentage
            device_count += 1
            
            # Calculate total power consumption from all devices
            if power_data and power_data.ain1_value is not None:
                # Use current AIN1 value as power consumption in kW
                total_consumption = power_data.ain1_value
                summary['total_power_consumption'] += total_consumption
            
            power_events = (power_data.power_loss_count_today if power_data else 0) + (power_data.power_restore_count_today if power_data else 0)
            summary['power_events_today'] += power_events
            
            summary['devices_data'].append(device_data)
        
        if device_count > 0:
            summary['avg_uptime_today'] = total_uptime / device_count
        
        # Get power events for today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_events = PowerEvent.objects.filter(
            device__in=devices,
            created_at__gte=today_start
        ).count()
        summary['power_events_today'] = today_events
        
        # Get unresolved power events
        summary['unresolved_events'] = PowerEvent.objects.filter(
            device__in=devices, is_resolved=False
        ).count()
        
        return summary
    
    def get_power_events_summary(self, device_id=None, factory_id=None, days=30):
        """Get power events summary"""
        events = PowerEvent.objects.all()
        
        if device_id:
            events = events.filter(device_id=device_id)
        elif factory_id:
            events = events.filter(device__factory_id=factory_id)
        
        # Filter by date range
        start_date = timezone.now() - timedelta(days=days)
        events = events.filter(created_at__gte=start_date)
        
        summary = {
            'total_events': events.count(),
            'unresolved_events': events.filter(is_resolved=False).count(),
            'power_loss_events': events.filter(event_type='power_loss').count(),
            'power_restored_events': events.filter(event_type='power_restored').count(),
            'critical_events': events.filter(severity='critical').count(),
            'high_severity_events': events.filter(severity='high').count(),
            'events_by_type': {},
            'events_by_severity': {},
            'recent_events': []
        }
        
        # Events by type
        for event_type, _ in PowerEvent.EVENT_TYPES:
            count = events.filter(event_type=event_type).count()
            summary['events_by_type'][event_type] = count
        
        # Events by severity
        for severity, _ in PowerEvent.SEVERITY_LEVELS:
            count = events.filter(severity=severity).count()
            summary['events_by_severity'][severity] = count
        
        # Recent events
        recent_events = events.order_by('-created_at')[:10]
        summary['recent_events'] = [
            {
                'id': event.id,
                'device_name': event.device.name,
                'event_type': event.get_event_type_display(),
                'severity': event.get_severity_display(),
                'message': event.message,
                'created_at': event.created_at,
                'is_resolved': event.is_resolved,
                'ain1_value': event.ain1_value
            }
            for event in recent_events
        ]
        
        return summary
    
    def resolve_power_event(self, event_id, user, notes=""):
        """Resolve a power event"""
        try:
            event = PowerEvent.objects.get(id=event_id)
            event.mark_as_resolved(user, notes)
            
            # Create notification for resolution
            self.create_power_event_notification(
                event, 
                f"Power event resolved by {user.username}",
                'low'
            )
            
            return True
        except PowerEvent.DoesNotExist:
            self.logger.error(f"PowerEvent with id {event_id} not found")
            return False
    
    def create_power_event_notification(self, event, message, priority='medium'):
        """Create notification for power event"""
        try:
            # Get notification category
            category, created = NotificationCategory.objects.get_or_create(
                name='Power Event',
                defaults={
                    'description': 'Power-related events and alerts',
                    'notification_type': 'device_alert',
                    'requires_admin': False,
                    'requires_super_admin': False,
                    'is_active': True
                }
            )
            
            # Get users who should be notified
            users_to_notify = []
            
            # Factory responsible users
            if event.device.factory:
                users_to_notify.extend(event.device.factory.responsible_users.all())
            
            # Users with power notification settings
            power_notification_users = PowerNotificationSettings.objects.filter(
                notify_power_loss=True if event.event_type == 'power_loss' else False,
                notify_power_restore=True if event.event_type == 'power_restored' else False
            ).values_list('user', flat=True)
            
            users_to_notify.extend(User.objects.filter(id__in=power_notification_users))
            
            # Remove duplicates
            users_to_notify = list(set(users_to_notify))
            
            # Create notifications
            for user in users_to_notify:
                Notification.objects.create(
                    user=user,
                    category=category,
                    title=f"Power Event: {event.get_event_type_display()}",
                    message=message,
                    priority=priority,
                    related_device=event.device,
                    related_factory=event.device.factory
                )
            
            return len(users_to_notify)
            
        except Exception as e:
            self.logger.error(f"Error creating power event notification: {e}")
            return 0
    
    def get_recent_power_events(self, factory_id=None, device_id=None, limit=10):
        """Get recent power events"""
        events = PowerEvent.objects.all()
        
        if factory_id:
            events = events.filter(device__factory_id=factory_id)
        
        if device_id:
            events = events.filter(device_id=device_id)
        
        return events.select_related('device', 'device__factory').order_by('-created_at')[:limit]
    
    def get_power_analytics(self, factory_id=None, days=30):
        """Get comprehensive power analytics"""
        devices = Device.objects.all()
        if factory_id:
            devices = devices.filter(factory_id=factory_id)
        
        start_date = timezone.now() - timedelta(days=days)
        
        analytics = {
            'period_days': days,
            'total_devices': devices.count(),
            'power_events': self.get_power_events_summary(factory_id=factory_id, days=days),
            'power_summary': self.get_device_power_summary(factory_id=factory_id),
            'trends': {},
            'top_issues': [],
            'recommendations': []
        }
        
        # Get power data trends
        power_data = PowerData.objects.filter(
            device__in=devices,
            last_mqtt_update__gte=start_date
        )
        
        if power_data.exists():
            # Get current power values for analytics
            current_power_values = [pd.ain1_value for pd in power_data if pd.ain1_value is not None]
            
            analytics['trends'] = {
                'avg_power_consumption': sum(current_power_values) / len(current_power_values) if current_power_values else 0,
                'max_power_consumption': max(current_power_values) if current_power_values else 0,
                'total_power_losses': power_data.aggregate(Count('power_loss_count_today'))['power_loss_count_today__count'] or 0,
                'total_power_restores': power_data.aggregate(Count('power_restore_count_today'))['power_restore_count_today__count'] or 0,
            }
        
        # Get top issues (devices with most power problems)
        devices_with_issues = power_data.filter(
            Q(power_loss_count_today__gt=0) | Q(power_loss_count_week__gt=0)
        ).order_by('-power_loss_count_today')[:5]
        
        analytics['top_issues'] = [
            {
                'device_name': pd.device.name,
                'power_losses_today': pd.power_loss_count_today,
                'power_losses_week': pd.power_loss_count_week,
                'uptime_percentage': pd.get_uptime_percentage_today(),
                'last_power_loss': pd.last_power_loss
            }
            for pd in devices_with_issues
        ]
        
        # Generate recommendations
        recommendations = []
        
        if analytics['power_events']['unresolved_events'] > 0:
            recommendations.append({
                'type': 'urgent',
                'message': f"Resolve {analytics['power_events']['unresolved_events']} unresolved power events"
            })
        
        if analytics['trends']['total_power_losses'] > 10:
            recommendations.append({
                'type': 'warning',
                'message': "High number of power losses detected. Check power infrastructure."
            })
        
        if analytics['power_summary']['avg_uptime_today'] < 95:
            recommendations.append({
                'type': 'info',
                'message': f"Average uptime is {analytics['power_summary']['avg_uptime_today']:.1f}%. Consider power backup solutions."
            })
        
        analytics['recommendations'] = recommendations
        
        return analytics
    
    def cleanup_old_power_events(self, days=90):
        """Clean up old power events"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_events = PowerEvent.objects.filter(
            created_at__lt=cutoff_date,
            is_resolved=True
        )
        
        count = old_events.count()
        old_events.delete()
        
        self.logger.info(f"Cleaned up {count} old power events older than {days} days")
        return count 