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
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            deleted_count = PowerEvent.objects.filter(created_at__lt=cutoff_date).delete()[0]
            self.logger.info(f"Cleaned up {deleted_count} old power events")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Error cleaning up old power events: {e}")
            return 0

    def get_suspicious_activity_analysis(self, device, check_interval_minutes=5):
        """
        Analyze suspicious activity when there's no power but counter is running.
        This implements the logic requested by the user:
        - Check if there's no power
        - Wait 5 minutes and check again
        - If still no power, check if there's production between the two checks
        - If there's production without power, it's suspicious
        - If no production, factory is just offline (normal)
        """
        try:
            from datetime import timedelta
            from mill.models import RawData, DevicePowerStatus
            
            # Get current time and calculate the check interval
            current_time = timezone.now()
            check_interval = timedelta(minutes=check_interval_minutes)
            
            # Get the latest power status
            power_status = DevicePowerStatus.objects.filter(device=device).first()
            if not power_status:
                return {
                    'has_suspicious_activity': False,
                    'message': 'No power status data available',
                    'analysis_data': None
                }
            
            # Check if device currently has no power
            if power_status.has_power:
                return {
                    'has_suspicious_activity': False,
                    'message': 'Device currently has power - no suspicious activity',
                    'analysis_data': None
                }
            
            # Get the time when power was lost
            power_loss_time = power_status.power_loss_detected_at
            if not power_loss_time:
                return {
                    'has_suspicious_activity': False,
                    'message': 'No power loss time recorded',
                    'analysis_data': None
                }
            
            # Calculate the check time (5 minutes after power loss)
            check_time = power_loss_time + check_interval
            
            # If we haven't reached the check time yet, return pending status
            if current_time < check_time:
                remaining_time = check_time - current_time
                return {
                    'has_suspicious_activity': False,
                    'message': f'Waiting for {check_interval_minutes}-minute check. {remaining_time.seconds // 60} minutes remaining.',
                    'analysis_data': None,
                    'pending_check': True,
                    'check_time': check_time
                }
            
            # Get counter data between power loss and check time
            start_time = power_loss_time
            end_time = check_time
            
            # Get raw data for this period
            raw_data = RawData.objects.filter(
                device=device,
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('timestamp')
            
            if not raw_data.exists():
                return {
                    'has_suspicious_activity': False,
                    'message': 'No data available for analysis period',
                    'analysis_data': None
                }
            
            # Get counter values at power loss time
            power_loss_record = raw_data.first()
            power_loss_counters = {
                'counter_1': power_loss_record.counter_1 or 0,
                'counter_2': power_loss_record.counter_2 or 0,
                'counter_3': power_loss_record.counter_3 or 0,
                'counter_4': power_loss_record.counter_4 or 0,
            }
            
            # Get counter values at check time (5 minutes later)
            check_record = raw_data.last()
            check_counters = {
                'counter_1': check_record.counter_1 or 0,
                'counter_2': check_record.counter_2 or 0,
                'counter_3': check_record.counter_3 or 0,
                'counter_4': check_record.counter_4 or 0,
            }
            
            # Calculate production during the no-power period
            production_during_no_power = {}
            total_production = 0
            has_suspicious_activity = False
            
            for counter_name in ['counter_1', 'counter_2', 'counter_3', 'counter_4']:
                power_loss_value = power_loss_counters[counter_name]
                check_value = check_counters[counter_name]
                production = check_value - power_loss_value
                
                if production > 0:
                    production_during_no_power[counter_name] = {
                        'power_loss_value': power_loss_value,
                        'check_value': check_value,
                        'production': production
                    }
                    total_production += production
                    has_suspicious_activity = True
            
            # Get all counter changes during the period for detailed analysis
            counter_changes_during_period = []
            previous_counters = power_loss_counters.copy()
            
            for record in raw_data[1:]:  # Skip first record
                changes = {}
                for counter_name in ['counter_1', 'counter_2', 'counter_3', 'counter_4']:
                    current_value = getattr(record, counter_name) or 0
                    previous_value = previous_counters[counter_name]
                    change = current_value - previous_value
                    
                    if change > 0:
                        changes[counter_name] = {
                            'previous': previous_value,
                            'current': current_value,
                            'change': change,
                            'timestamp': record.timestamp,
                            'ain1_value': record.ain1_value
                        }
                    
                    previous_counters[counter_name] = current_value
                
                if changes:
                    counter_changes_during_period.append({
                        'timestamp': record.timestamp,
                        'changes': changes,
                        'ain1_value': record.ain1_value
                    })
            
            analysis_data = {
                'power_loss_time': power_loss_time,
                'check_time': check_time,
                'power_loss_counters': power_loss_counters,
                'check_counters': check_counters,
                'production_during_no_power': production_during_no_power,
                'total_production': total_production,
                'counter_changes_during_period': counter_changes_during_period,
                'check_interval_minutes': check_interval_minutes
            }
            
            if has_suspicious_activity:
                message = f"CRITICAL: {total_production} bags produced during {check_interval_minutes}-minute no-power period!"
            else:
                message = f"Factory is offline (normal) - no production during {check_interval_minutes}-minute no-power period"
            
            return {
                'has_suspicious_activity': has_suspicious_activity,
                'message': message,
                'analysis_data': analysis_data
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing suspicious activity for device {device.id}: {str(e)}")
            return {
                'has_suspicious_activity': False,
                'message': f'Error during analysis: {str(e)}',
                'analysis_data': None
            }

    def get_device_offline_analysis(self, device):
        """
        Analyze device offline status and show:
        - How long device has been offline without counter activity
        - How long device has been running without power but with counter activity
        - Current status and recommendations
        """
        try:
            from datetime import timedelta
            from mill.models import RawData, DevicePowerStatus
            
            # Get current time
            current_time = timezone.now()
            
            # Get the latest power status
            power_status = DevicePowerStatus.objects.filter(device=device).first()
            if not power_status:
                return {
                    'has_data': False,
                    'message': 'No power status data available',
                    'analysis_data': None
                }
            
            # Get the last 24 hours of raw data
            start_time = current_time - timedelta(hours=24)
            raw_data = RawData.objects.filter(
                device=device,
                timestamp__gte=start_time
            ).order_by('timestamp')
            
            if not raw_data.exists():
                return {
                    'has_data': False,
                    'message': 'No data available for the last 24 hours',
                    'analysis_data': None
                }
            
            # Analyze offline periods
            offline_periods = []
            current_offline_start = None
            current_offline_type = None
            
            # Get power loss time if device is currently offline
            power_loss_time = power_status.power_loss_detected_at if not power_status.has_power else None
            
            for record in raw_data:
                has_power = record.ain1_value > 0 if record.ain1_value is not None else False
                
                # Check if there's counter activity
                has_counter_activity = any([
                    record.counter_1 and record.counter_1 > 0,
                    record.counter_2 and record.counter_2 > 0,
                    record.counter_3 and record.counter_3 > 0,
                    record.counter_4 and record.counter_4 > 0
                ])
                
                # Determine offline type
                if not has_power:
                    if has_counter_activity:
                        offline_type = 'no_power_with_counter'
                    else:
                        offline_type = 'no_power_no_counter'
                else:
                    offline_type = 'online'
                
                # Track offline periods
                if offline_type != 'online':
                    if current_offline_start is None:
                        current_offline_start = record.timestamp
                        current_offline_type = offline_type
                else:
                    if current_offline_start is not None:
                        # End of offline period
                        offline_periods.append({
                            'start_time': current_offline_start,
                            'end_time': record.timestamp,
                            'duration': record.timestamp - current_offline_start,
                            'type': current_offline_type,
                            'counter_activity': current_offline_type == 'no_power_with_counter'
                        })
                        current_offline_start = None
                        current_offline_type = None
            
            # Handle current offline period if device is still offline
            if current_offline_start is not None:
                offline_periods.append({
                    'start_time': current_offline_start,
                    'end_time': current_time,
                    'duration': current_time - current_offline_start,
                    'type': current_offline_type,
                    'counter_activity': current_offline_type == 'no_power_with_counter',
                    'is_current': True
                })
            
            # Calculate statistics
            total_offline_time = timedelta()
            total_no_power_with_counter_time = timedelta()
            total_no_power_no_counter_time = timedelta()
            
            for period in offline_periods:
                total_offline_time += period['duration']
                if period['type'] == 'no_power_with_counter':
                    total_no_power_with_counter_time += period['duration']
                elif period['type'] == 'no_power_no_counter':
                    total_no_power_no_counter_time += period['duration']
            
            # Get current status
            current_status = 'online'
            current_offline_duration = None
            
            if not power_status.has_power:
                if power_loss_time:
                    current_offline_duration = current_time - power_loss_time
                    # Check if there's been counter activity since power loss
                    recent_data = raw_data.filter(timestamp__gte=power_loss_time)
                    has_recent_counter_activity = False
                    
                    for record in recent_data:
                        if any([
                            record.counter_1 and record.counter_1 > 0,
                            record.counter_2 and record.counter_2 > 0,
                            record.counter_3 and record.counter_3 > 0,
                            record.counter_4 and record.counter_4 > 0
                        ]):
                            has_recent_counter_activity = True
                            break
                    
                    if has_recent_counter_activity:
                        current_status = 'no_power_with_counter'
                    else:
                        current_status = 'no_power_no_counter'
            
            # Generate recommendations
            recommendations = []
            if current_status == 'no_power_with_counter':
                recommendations.append({
                    'type': 'critical',
                    'message': 'Device is running without power but counter is active - CRITICAL ISSUE!'
                })
            elif current_status == 'no_power_no_counter':
                recommendations.append({
                    'type': 'info',
                    'message': 'Device is offline (normal) - no counter activity detected'
                })
            
            if total_no_power_with_counter_time > timedelta(minutes=30):
                recommendations.append({
                    'type': 'warning',
                    'message': f'Device has been running without power for {total_no_power_with_counter_time} in the last 24 hours'
                })
            
            analysis_data = {
                'current_status': current_status,
                'current_offline_duration': current_offline_duration,
                'power_loss_time': power_loss_time,
                'offline_periods': offline_periods,
                'total_offline_time': total_offline_time,
                'total_no_power_with_counter_time': total_no_power_with_counter_time,
                'total_no_power_no_counter_time': total_no_power_no_counter_time,
                'recommendations': recommendations,
                'analysis_period': '24 hours'
            }
            
            return {
                'has_data': True,
                'message': f'Device is currently {current_status.replace("_", " ").title()}',
                'analysis_data': analysis_data
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing device offline status for device {device.id}: {str(e)}")
            return {
                'has_data': False,
                'message': f'Error during analysis: {str(e)}',
                'analysis_data': None
            } 

    def get_device_detailed_power_analysis(self, device):
        """
        Get detailed power analysis for a specific device including:
        - Current power status
        - Counter activity during power loss periods
        - Production without power incidents
        - Historical power events
        """
        try:
            from mill.models import RawData
            
            current_time = timezone.now()
            power_status = DevicePowerStatus.objects.filter(device=device).first()
            
            # Get raw data for the last 7 days
            start_time = current_time - timedelta(days=7)
            raw_data = RawData.objects.filter(
                device=device, 
                timestamp__gte=start_time
            ).order_by('timestamp')
            
            if not raw_data.exists():
                return {
                    'has_data': False,
                    'message': 'No data available for the last 7 days',
                    'device': device,
                    'current_status': 'unknown'
                }
            
            # Analyze power and counter data
            power_incidents = []
            current_incident = None
            
            for record in raw_data:
                has_power = record.ain1_value > 0 if record.ain1_value is not None else False
                counter_values = [
                    getattr(record, f'counter_{i}', 0) or 0 
                    for i in range(1, 5)
                ]
                total_counter = sum(counter_values)
                
                if not has_power:
                    if current_incident is None:
                        # Start new power loss incident
                        current_incident = {
                            'start_time': record.timestamp,
                            'start_counter': total_counter,
                            'has_counter_activity': False,
                            'counter_changes': [],
                            'end_time': None,
                            'end_counter': None,
                            'total_production': 0
                        }
                    else:
                        # Continue existing incident
                        if total_counter > current_incident['start_counter']:
                            counter_change = total_counter - current_incident['start_counter']
                            current_incident['counter_changes'].append({
                                'timestamp': record.timestamp,
                                'counter_value': total_counter,
                                'change': counter_change
                            })
                            current_incident['has_counter_activity'] = True
                            current_incident['total_production'] = total_counter - current_incident['start_counter']
                else:
                    if current_incident is not None:
                        # End power loss incident
                        current_incident['end_time'] = record.timestamp
                        current_incident['end_counter'] = total_counter
                        current_incident['duration'] = record.timestamp - current_incident['start_time']
                        
                        # Only include if there was counter activity or duration > 10 minutes
                        if (current_incident['has_counter_activity'] or 
                            current_incident['duration'] > timedelta(minutes=10)):
                            power_incidents.append(current_incident)
                        
                        current_incident = None
            
            # Handle ongoing incident
            if current_incident is not None:
                current_incident['end_time'] = current_time
                current_incident['duration'] = current_time - current_incident['start_time']
                current_incident['is_ongoing'] = True
                
                if (current_incident['has_counter_activity'] or 
                    current_incident['duration'] > timedelta(minutes=10)):
                    power_incidents.append(current_incident)
            
            # Calculate statistics
            total_incidents = len(power_incidents)
            incidents_with_counter = len([i for i in power_incidents if i['has_counter_activity']])
            total_production_without_power = sum(i['total_production'] for i in power_incidents if i['has_counter_activity'])
            total_downtime = sum(i['duration'] for i in power_incidents)
            
            # Current status
            current_status = 'online'
            if power_status and not power_status.has_power:
                if power_status.power_loss_detected_at:
                    downtime = current_time - power_status.power_loss_detected_at
                    if downtime > timedelta(minutes=10):
                        current_status = 'offline'
                    else:
                        current_status = 'power_loss'
            
            # Get recent power events
            recent_events = PowerEvent.objects.filter(device=device).order_by('-created_at')[:10]
            
            return {
                'has_data': True,
                'device': device,
                'current_status': current_status,
                'power_status': power_status,
                'power_incidents': power_incidents,
                'statistics': {
                    'total_incidents': total_incidents,
                    'incidents_with_counter': incidents_with_counter,
                    'total_production_without_power': total_production_without_power,
                    'total_downtime': total_downtime,
                    'avg_incident_duration': total_downtime / total_incidents if total_incidents > 0 else timedelta(0)
                },
                'recent_events': recent_events,
                'analysis_period': '7 days'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing device power for {device.name}: {str(e)}")
            return {
                'has_data': False,
                'message': f'Error during analysis: {str(e)}',
                'device': device,
                'current_status': 'error'
            } 

    def get_all_devices_without_power(self):
        """
        Get all devices currently without power and their detailed status
        Returns devices with power issues and their statistics
        """
        try:
            devices_without_power = []
            
            # Get all devices with their power status
            devices = Device.objects.select_related('factory').all()
            
            for device in devices:
                power_status = DevicePowerStatus.objects.filter(device=device).first()
                
                if power_status and not power_status.has_power:
                    # Get detailed analysis for this device
                    detailed_analysis = self.get_device_detailed_power_analysis(device)
                    
                    device_info = {
                        'device': device,
                        'power_status': power_status,
                        'power_loss_detected_at': power_status.power_loss_detected_at,
                        'downtime_duration': timezone.now() - power_status.power_loss_detected_at if power_status.power_loss_detected_at else None,
                        'production_during_power_loss': power_status.production_during_power_loss,
                        'detailed_analysis': detailed_analysis,
                        'factory': device.factory,
                        'severity': 'critical' if detailed_analysis.get('statistics', {}).get('incidents_with_counter', 0) > 0 else 'warning'
                    }
                    
                    devices_without_power.append(device_info)
            
            # Sort by severity (critical first) then by downtime duration
            devices_without_power.sort(key=lambda x: (
                x['severity'] == 'critical', 
                x['downtime_duration'] or timedelta(0)
            ), reverse=True)
            
            return devices_without_power
            
        except Exception as e:
            self.logger.error(f"Error getting devices without power: {str(e)}")
            return [] 