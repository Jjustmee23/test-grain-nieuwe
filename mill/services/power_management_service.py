from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from mill.models import (
    Device, RawData, PowerEvent, DevicePowerStatus, PowerNotificationSettings,
    Notification, NotificationCategory, EmailHistory, ProductionData
)
from mill.services.notification_service import NotificationService
from mill.services.simple_email_service import SimpleEmailService
import logging

logger = logging.getLogger(__name__)

class PowerManagementService:
    """Service for managing device power status and events"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.email_service = SimpleEmailService()
    
    def process_raw_data(self, raw_data):
        """Process new raw data and check for power events"""
        try:
            device = raw_data.device
            ain1_value = raw_data.ain1_value
            
            # Get or create power status for device
            power_status, created = DevicePowerStatus.objects.get_or_create(
                device=device,
                defaults={'power_threshold': 0.0}
            )
            
            # Update power status based on ain1_value
            status_changed = power_status.update_power_status(ain1_value)
            
            # Check for production without power
            counter_values = {
                'counter_1': raw_data.counter_1,
                'counter_2': raw_data.counter_2,
                'counter_3': raw_data.counter_3,
                'counter_4': raw_data.counter_4,
            }
            
            production_without_power = power_status.check_production_without_power(counter_values)
            
            # Handle power events
            if status_changed:
                if not power_status.has_power:
                    self._handle_power_loss(device, ain1_value, raw_data)
                else:
                    self._handle_power_restore(device, ain1_value, raw_data)
            
            # Handle production without power
            if production_without_power:
                self._handle_production_without_power(device, ain1_value, raw_data)
                
        except Exception as e:
            logger.error(f"Error processing power data for device {raw_data.device.id}: {str(e)}")
    
    def update_power_status_from_database(self, device=None):
        """Update power status for all devices or a specific device based on latest ain1_value data"""
        try:
            if device:
                devices = [device]
            else:
                # Get all devices that belong to factories
                devices = Device.objects.filter(factory__isnull=False)
            
            updated_count = 0
            
            for device in devices:
                try:
                    # Get the latest RawData entry for this device
                    latest_raw_data = RawData.objects.filter(
                        device=device,
                        ain1_value__isnull=False
                    ).order_by('-timestamp').first()
                    
                    # Get or create power status
                    power_status, created = DevicePowerStatus.objects.get_or_create(
                        device=device,
                        defaults={'power_threshold': 0.0}
                    )
                    
                    # Check if device is offline (no data for more than 10 minutes)
                    offline_threshold = timezone.now() - timezone.timedelta(minutes=10)
                    is_offline = False
                    
                    if latest_raw_data:
                        # Check if data is older than 10 minutes
                        if latest_raw_data.timestamp and latest_raw_data.timestamp < offline_threshold:
                            is_offline = True
                            power_status.has_power = False
                            power_status.ain1_value = 0.0
                            power_status.last_power_check = latest_raw_data.timestamp
                            
                            # Handle offline status
                            if not power_status.power_loss_detected_at:
                                power_status.power_loss_detected_at = offline_threshold
                                power_status.power_restored_at = None
                                
                                # Create offline event
                                self._handle_device_offline(device, latest_raw_data)
                            
                            power_status.save()
                            updated_count += 1
                            logger.info(f"Device {device.name} marked as offline (no data for >10 minutes)")
                            continue
                        
                        # Device is online, process power status
                        if latest_raw_data.ain1_value is not None:
                            previous_has_power = power_status.has_power
                            power_status.ain1_value = latest_raw_data.ain1_value
                            power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
                            
                            # Determine if device has power (anything > 0 is power)
                            # According to user: everything above 0 is power, 0 or below is no power
                            # 0.0001 is also power
                            if latest_raw_data.ain1_value is not None:
                                power_status.has_power = latest_raw_data.ain1_value > 0
                            else:
                                power_status.has_power = False
                            
                            # Handle power loss
                            if not power_status.has_power and previous_has_power:
                                power_status.power_loss_detected_at = latest_raw_data.timestamp or timezone.now()
                                power_status.power_restored_at = None
                                
                                # Create power loss event
                                self._handle_power_loss(device, latest_raw_data.ain1_value, latest_raw_data)
                                
                            # Handle power restoration
                            elif power_status.has_power and not previous_has_power:
                                power_status.power_restored_at = latest_raw_data.timestamp or timezone.now()
                                
                                # Create power restore event
                                self._handle_power_restore(device, latest_raw_data.ain1_value, latest_raw_data)
                            
                            power_status.save()
                            updated_count += 1
                            
                            logger.info(f"Updated power status for device {device.name}: ain1_value={latest_raw_data.ain1_value}, has_power={power_status.has_power}")
                    else:
                        # No data at all - mark as offline
                        power_status.has_power = False
                        power_status.ain1_value = 0.0
                        power_status.last_power_check = timezone.now()
                        
                        if not power_status.power_loss_detected_at:
                            power_status.power_loss_detected_at = timezone.now()
                            power_status.power_restored_at = None
                            
                            # Create offline event
                            self._handle_device_offline(device, None)
                        
                        power_status.save()
                        updated_count += 1
                        logger.info(f"Device {device.name} marked as offline (no data available)")
                    
                except Exception as e:
                    logger.error(f"Error updating power status for device {device.name}: {str(e)}")
                    continue
            
            logger.info(f"Updated power status for {updated_count} devices")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error in update_power_status_from_database: {str(e)}")
            return 0
    
    def get_power_consumption_data(self, device, days=30):
        """Get power consumption data for a device over the specified period"""
        try:
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=days)
            
            raw_data = RawData.objects.filter(
                device=device,
                timestamp__gte=start_date,
                timestamp__lte=end_date,
                ain1_value__isnull=False
            ).order_by('timestamp')
            
            power_data = []
            for data in raw_data:
                power_data.append({
                    'timestamp': data.timestamp,
                    'ain1_value': data.ain1_value,
                    'has_power': data.ain1_value > 0
                })
            
            return power_data
            
        except Exception as e:
            logger.error(f"Error getting power consumption data for device {device.name}: {str(e)}")
            return []
    
    def calculate_power_statistics(self, device, days=30):
        """Calculate power statistics for a device"""
        try:
            power_data = self.get_power_consumption_data(device, days)
            
            if not power_data:
                return {
                    'avg_power': 0,
                    'max_power': 0,
                    'min_power': 0,
                    'total_readings': 0,
                    'power_on_time': 0,
                    'power_off_time': 0,
                    'uptime_percentage': 0
                }
            
            power_values = [data['ain1_value'] for data in power_data]
            power_on_readings = len([data for data in power_data if data['has_power']])
            total_readings = len(power_data)
            
            return {
                'avg_power': sum(power_values) / len(power_values) if power_values else 0,
                'max_power': max(power_values) if power_values else 0,
                'min_power': min(power_values) if power_values else 0,
                'total_readings': total_readings,
                'power_on_time': power_on_readings,
                'power_off_time': total_readings - power_on_readings,
                'uptime_percentage': (power_on_readings / total_readings * 100) if total_readings > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating power statistics for device {device.name}: {str(e)}")
            return {}
    
    def _handle_power_loss(self, device, ain1_value, raw_data):
        """Handle power loss event"""
        try:
            # Create power event
            event = PowerEvent.objects.create(
                device=device,
                event_type='power_loss',
                severity='high',
                ain1_value=ain1_value,
                counter_1_value=raw_data.counter_1,
                counter_2_value=raw_data.counter_2,
                counter_3_value=raw_data.counter_3,
                counter_4_value=raw_data.counter_4,
                message=f"Power loss detected on device {device.name}. AIN1 value: {ain1_value}"
            )
            
            # Send notifications (temporarily disabled)
            # self._send_power_loss_notifications(device, event)
            
            logger.info(f"Power loss event created for device {device.id}")
            
        except Exception as e:
            logger.error(f"Error handling power loss for device {device.id}: {str(e)}")
    
    def _handle_power_restore(self, device, ain1_value, raw_data):
        """Handle power restore event"""
        try:
            # Create power event
            event = PowerEvent.objects.create(
                device=device,
                event_type='power_restored',
                severity='medium',
                ain1_value=ain1_value,
                counter_1_value=raw_data.counter_1,
                counter_2_value=raw_data.counter_2,
                counter_3_value=raw_data.counter_3,
                counter_4_value=raw_data.counter_4,
                message=f"Power restored on device {device.name}. AIN1 value: {ain1_value}"
            )
            
            # Send notifications (temporarily disabled)
            # self._send_power_restore_notifications(device, event)
            
            logger.info(f"Power restore event created for device {device.id}")
            
        except Exception as e:
            logger.error(f"Error handling power restore for device {device.id}: {str(e)}")
    
    def _handle_device_offline(self, device, raw_data):
        """Handle device offline event (no data for more than 10 minutes)"""
        try:
            # Create power event with low severity and no message
            event = PowerEvent.objects.create(
                device=device,
                event_type='power_loss',
                severity='low',
                ain1_value=0.0,
                counter_1_value=raw_data.counter_1 if raw_data else None,
                counter_2_value=raw_data.counter_2 if raw_data else None,
                counter_3_value=raw_data.counter_3 if raw_data else None,
                counter_4_value=raw_data.counter_4 if raw_data else None,
                message=""  # No message for offline devices
            )
            
            # Send notifications to factory responsible users
            self._send_device_offline_notifications(device, event)
            
            logger.info(f"Device offline event created for device {device.id}")
            
        except Exception as e:
            logger.error(f"Error handling device offline for device {device.id}: {str(e)}")
    
    def _handle_production_without_power(self, device, ain1_value, raw_data):
        """Handle production without power event"""
        try:
            # Create power event
            event = PowerEvent.objects.create(
                device=device,
                event_type='production_without_power',
                severity='critical',
                ain1_value=ain1_value,
                counter_1_value=raw_data.counter_1,
                counter_2_value=raw_data.counter_2,
                counter_3_value=raw_data.counter_3,
                counter_4_value=raw_data.counter_4,
                message=f"CRITICAL: Production detected without power on device {device.name}. This indicates a serious system issue."
            )
            
            # Send notifications to factory responsible users and super admins
            self._send_production_without_power_notifications(device, event)
            
            logger.warning(f"Production without power event created for device {device.id}")
            
        except Exception as e:
            logger.error(f"Error handling production without power for device {device.id}: {str(e)}")
    
    def _send_power_loss_notifications(self, device, event):
        """Send power loss notifications to responsible users"""
        try:
            # Get notification category
            category, _ = NotificationCategory.objects.get_or_create(
                notification_type='device_alert',
                defaults={
                    'name': 'Device Alert',
                    'description': 'Alerts related to device status and power'
                }
            )
            
            # Get responsible users
            responsible_users = self._get_responsible_users(device)
            
            for user in responsible_users:
                # Check user preferences
                settings, _ = PowerNotificationSettings.objects.get_or_create(user=user)
                
                if settings.notify_power_loss:
                    # Create in-app notification
                    notification = Notification.objects.create(
                        user=user,
                        category=category,
                        title=f"Power Loss Alert - {device.name}",
                        message=f"Device {device.name} has lost power. AIN1 value: {event.ain1_value}",
                        priority='high',
                        related_device=device,
                        link=f'/manage-devices/'
                    )
                    
                    # Send email if enabled
                    if settings.email_power_loss:
                        self._send_power_loss_email(user, device, event)
                    
                    event.notification_sent = True
                    event.save()
                    
        except Exception as e:
            logger.error(f"Error sending power loss notifications: {str(e)}")
    
    def _send_power_restore_notifications(self, device, event):
        """Send power restore notifications to responsible users"""
        try:
            # Get notification category
            category, _ = NotificationCategory.objects.get_or_create(
                notification_type='device_alert',
                defaults={
                    'name': 'Device Alert',
                    'description': 'Alerts related to device status and power'
                }
            )
            
            # Get responsible users
            responsible_users = self._get_responsible_users(device)
            
            for user in responsible_users:
                # Check user preferences
                settings, _ = PowerNotificationSettings.objects.get_or_create(user=user)
                
                if settings.notify_power_restore:
                    # Create in-app notification
                    notification = Notification.objects.create(
                        user=user,
                        category=category,
                        title=f"Power Restored - {device.name}",
                        message=f"Power has been restored on device {device.name}. AIN1 value: {event.ain1_value}",
                        priority='medium',
                        related_device=device,
                        link=f'/manage-devices/'
                    )
                    
                    # Send email if enabled
                    if settings.email_power_restore:
                        self._send_power_restore_email(user, device, event)
                    
                    event.notification_sent = True
                    event.save()
                    
        except Exception as e:
            logger.error(f"Error sending power restore notifications: {str(e)}")
    
    def _send_device_offline_notifications(self, device, event):
        """Send device offline notifications to responsible users"""
        try:
            # Get notification category
            category, _ = NotificationCategory.objects.get_or_create(
                notification_type='device_alert',
                defaults={
                    'name': 'Device Alert',
                    'description': 'Alerts related to device status and power'
                }
            )
            
            # Get responsible users
            responsible_users = self._get_responsible_users(device)
            
            for user in responsible_users:
                # Check user preferences
                settings, _ = PowerNotificationSettings.objects.get_or_create(user=user)
                
                if settings.notify_power_loss:
                    # Create in-app notification
                    notification = Notification.objects.create(
                        user=user,
                        category=category,
                        title=f"Device Offline - {device.name}",
                        message=f"Device {device.name} is offline - no data received for more than 10 minutes. This indicates a communication or power issue.",
                        priority='high',
                        related_device=device,
                        link=f'/manage-devices/'
                    )
                    
                    # Send email if enabled
                    if settings.email_power_loss:
                        self._send_device_offline_email(user, device, event)
                    
                    event.notification_sent = True
                    event.save()
                    
        except Exception as e:
            logger.error(f"Error sending device offline notifications: {str(e)}")
    
    def _send_production_without_power_notifications(self, device, event):
        """Send production without power notifications to super admins"""
        try:
            # Get notification category
            category, _ = NotificationCategory.objects.get_or_create(
                notification_type='system_warning',
                defaults={
                    'name': 'System Warning',
                    'description': 'Critical system warnings and errors'
                }
            )
            
            # Get all super admins
            super_admins = User.objects.filter(is_superuser=True)
            
            for user in super_admins:
                # Create in-app notification
                notification = Notification.objects.create(
                    user=user,
                    category=category,
                    title=f"CRITICAL: Production Without Power - {device.name}",
                    message=f"Device {device.name} is showing production activity without power. This indicates a serious system malfunction.",
                    priority='urgent',
                    related_device=device,
                    link=f'/manage-devices/'
                )
                
                # Send email
                self._send_production_without_power_email(user, device, event)
                
                event.super_admin_notified = True
                event.save()
                
        except Exception as e:
            logger.error(f"Error sending production without power notifications: {str(e)}")
    
    def _get_responsible_users(self, device):
        """Get users responsible for a device"""
        try:
            # Get factory responsible users
            factory_users = []
            if device.factory:
                factory_users = list(device.factory.responsible_users.all())
            
            # Get super admins
            super_admins = list(User.objects.filter(is_superuser=True))
            
            # Get users with power management permissions
            power_users = list(PowerManagementPermission.objects.filter(
                can_access_power_management=True
            ).values_list('user', flat=True))
            
            # Get users with specific device assignments
            device_users = list(PowerNotificationSettings.objects.filter(
                responsible_devices=device
            ).values_list('user', flat=True))
            
            # Combine all users
            all_users = factory_users + super_admins
            
            # Add power management users and device users
            if power_users:
                all_users.extend(User.objects.filter(id__in=power_users))
            if device_users:
                all_users.extend(User.objects.filter(id__in=device_users))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_users = []
            for user in all_users:
                if user.id not in seen:
                    seen.add(user.id)
                    unique_users.append(user)
            
            return unique_users
            
        except Exception as e:
            logger.error(f"Error getting responsible users for device {device.id}: {str(e)}")
            return []
    
    def _send_power_loss_email(self, user, device, event):
        """Send power loss email notification"""
        try:
            subject = f"Power Loss Alert - Device {device.name}"
            
            message = f"""
Power Loss Alert

Device: {device.name}
Factory: {device.factory.name if device.factory else 'Unknown'}
AIN1 Value: {event.ain1_value}
Time: {event.created_at}

The device has lost power. Please check the device and electrical connections.

This is an automated alert from the Mill Application Power Management System.
            """
            
            # Send email
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_content=message,
                text_content=message,
                user=user
            )
            
            event.email_sent = True
            event.save()
            
            logger.info(f"Power loss email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending power loss email to {user.email}: {str(e)}")
    
    def _send_power_restore_email(self, user, device, event):
        """Send power restore email notification"""
        try:
            subject = f"Power Restored - Device {device.name}"
            
            message = f"""
Power Restored

Device: {device.name}
Factory: {device.factory.name if device.factory else 'Unknown'}
AIN1 Value: {event.ain1_value}
Time: {event.created_at}

Power has been restored to the device.

This is an automated alert from the Mill Application Power Management System.
            """
            
            # Send email
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_content=message,
                text_content=message,
                user=user
            )
            
            event.email_sent = True
            event.save()
            
            logger.info(f"Power restore email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending power restore email to {user.email}: {str(e)}")
    
    def _send_device_offline_email(self, user, device, event):
        """Send device offline email notification"""
        try:
            subject = f"Device Offline Alert - {device.name}"
            
            message = f"""
Device Offline Alert

Device: {device.name}
Factory: {device.factory.name if device.factory else 'Unknown'}
Time: {event.created_at}

The device is offline - no data has been received for more than 10 minutes.
This indicates a communication or power issue that requires attention.

Last Known Data:
- Power Value (AIN1): {event.ain1_value}
- Counter 1: {event.counter_1_value}
- Counter 2: {event.counter_2_value}
- Counter 3: {event.counter_3_value}
- Counter 4: {event.counter_4_value}

Please check the device connection and power supply.

This is an automated alert from the Mill Application Power Management System.
            """
            
            # Send email
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_content=message,
                text_content=message,
                user=user
            )
            
            event.email_sent = True
            event.save()
            
            logger.info(f"Device offline email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending device offline email to {user.email}: {str(e)}")
    
    def _send_production_without_power_email(self, user, device, event):
        """Send production without power email notification"""
        try:
            subject = f"CRITICAL: Production Without Power - {device.name}"
            
            message = f"""
CRITICAL ALERT: Production Without Power

Device: {device.name}
Factory: {device.factory.name if device.factory else 'Unknown'}
Time: {event.created_at}

CRITICAL: Production has been detected on this device while it has no power.
This indicates a serious system issue that requires immediate attention.

Power Data:
- AIN1 Value: {event.ain1_value}
- Power Status: NO POWER

Production Data:
- Counter 1: {event.counter_1_value}
- Counter 2: {event.counter_2_value}
- Counter 3: {event.counter_3_value}
- Counter 4: {event.counter_4_value}

This is a critical issue that may indicate:
1. Sensor malfunction
2. Data corruption
3. System tampering
4. Electrical issues

Please investigate immediately.

This is an automated alert from the Mill Application Power Management System.
            """
            
            # Send email
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                html_content=message,
                text_content=message,
                user=user
            )
            
            event.email_sent = True
            event.save()
            
            logger.info(f"Production without power email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending production without power email to {user.email}: {str(e)}")
    
    def get_device_power_status(self, device):
        """Get current power status for a device"""
        try:
            return DevicePowerStatus.objects.get(device=device)
        except DevicePowerStatus.DoesNotExist:
            return None
    
    def get_active_power_events(self, device=None):
        """Get active (unresolved) power events - only for devices with factories"""
        try:
            queryset = PowerEvent.objects.filter(
                is_resolved=False,
                device__factory__isnull=False
            )
            if device:
                queryset = queryset.filter(device=device)
            return queryset
        except Exception as e:
            logger.error(f"Error getting active power events: {str(e)}")
            return PowerEvent.objects.none()
    
    def get_power_events_summary(self):
        """Get summary of power events"""
        try:
            total_events = PowerEvent.objects.count()
            unresolved_events = PowerEvent.objects.filter(is_resolved=False).count()
            critical_events = PowerEvent.objects.filter(
                severity='critical',
                is_resolved=False
            ).count()
            
            # Get power status summary - only devices with factories
            total_devices = Device.objects.filter(factory__isnull=False).count()
            devices_with_power = DevicePowerStatus.objects.filter(
                device__factory__isnull=False, 
                has_power=True
            ).count()
            devices_without_power = DevicePowerStatus.objects.filter(
                device__factory__isnull=False, 
                has_power=False
            ).count()
            
            return {
                'total_events': total_events,
                'unresolved_events': unresolved_events,
                'critical_events': critical_events,
                'total_devices': total_devices,
                'devices_with_power': devices_with_power,
                'devices_without_power': devices_without_power,
            }
        except Exception as e:
            logger.error(f"Error getting power events summary: {str(e)}")
            return {
                'total_events': 0, 
                'unresolved_events': 0, 
                'critical_events': 0,
                'total_devices': 0,
                'devices_with_power': 0,
                'devices_without_power': 0,
            }
    
    def get_device_counter_changes(self, device, hours=24):
        """Get counter changes for a device in the last N hours"""
        try:
            from datetime import timedelta
            
            # Get the last N hours of data
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get raw data for this device in the time range
            raw_data = RawData.objects.filter(
                device=device,
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('timestamp')
            
            if not raw_data.exists():
                return {
                    'counter_changes': [],
                    'production_without_power': [],
                    'total_bags_produced': 0,
                    'bags_without_power': 0
                }
            
            counter_changes = []
            production_without_power = []
            total_bags_produced = 0
            bags_without_power = 0
            
            # Get the first record as baseline
            first_record = raw_data.first()
            previous_counters = {
                'counter_1': first_record.counter_1 or 0,
                'counter_2': first_record.counter_2 or 0,
                'counter_3': first_record.counter_3 or 0,
                'counter_4': first_record.counter_4 or 0,
            }
            
            for record in raw_data[1:]:  # Skip first record
                # Calculate changes
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
                            'has_power': record.ain1_value > 0 if record.ain1_value is not None else False
                        }
                        
                        # Track production without power
                        if record.ain1_value is not None and record.ain1_value <= 0:
                            production_without_power.append({
                                'timestamp': record.timestamp,
                                'counter': counter_name,
                                'change': change,
                                'ain1_value': record.ain1_value
                            })
                            bags_without_power += change
                        
                        total_bags_produced += change
                    
                    # Update previous value
                    previous_counters[counter_name] = current_value
                
                if changes:
                    counter_changes.append({
                        'timestamp': record.timestamp,
                        'changes': changes,
                        'ain1_value': record.ain1_value
                    })
            
            return {
                'counter_changes': counter_changes,
                'production_without_power': production_without_power,
                'total_bags_produced': total_bags_produced,
                'bags_without_power': bags_without_power,
                'time_range': f"Last {hours} hours"
            }
            
        except Exception as e:
            logger.error(f"Error getting counter changes for device {device.id}: {str(e)}")
            return {
                'counter_changes': [],
                'production_without_power': [],
                'total_bags_produced': 0,
                'bags_without_power': 0,
                'error': str(e)
            }

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
            logger.error(f"Error analyzing suspicious activity for device {device.id}: {str(e)}")
            return {
                'has_suspicious_activity': False,
                'message': f'Error during analysis: {str(e)}',
                'analysis_data': None
            } 