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
            
            # Update power status
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
            
            # Send notifications
            self._send_power_loss_notifications(device, event)
            
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
            
            # Send notifications
            self._send_power_restore_notifications(device, event)
            
            logger.info(f"Power restore event created for device {device.id}")
            
        except Exception as e:
            logger.error(f"Error handling power restore for device {device.id}: {str(e)}")
    
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
            
            # Send notifications to super admins
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
            # Get users directly assigned to this device
            device_users = User.objects.filter(
                power_notification_settings__responsible_devices=device
            )
            
            # Get users responsible for the factory
            factory_users = User.objects.filter(
                power_notification_settings__responsible_devices__factory=device.factory
            )
            
            # Get super admins
            super_admins = User.objects.filter(is_superuser=True)
            
            # Combine all users
            all_users = list(device_users) + list(factory_users) + list(super_admins)
            
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
            Time: {event.created_at}
            AIN1 Value: {event.ain1_value}
            
            The device has lost power. Please check the device and electrical connections.
            
            This is an automated alert from the Mill Management System.
            """
            
            # Send email
            success = self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                message=message,
                email_type='system_alert'
            )
            
            if success:
                event.email_sent = True
                event.save()
                
                # Log email
                EmailHistory.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    email_type='system_alert',
                    status='sent'
                )
                
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
            Time: {event.created_at}
            AIN1 Value: {event.ain1_value}
            
            Power has been restored to the device.
            
            This is an automated alert from the Mill Management System.
            """
            
            # Send email
            success = self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                message=message,
                email_type='system_alert'
            )
            
            if success:
                event.email_sent = True
                event.save()
                
                # Log email
                EmailHistory.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    email_type='system_alert',
                    status='sent'
                )
                
        except Exception as e:
            logger.error(f"Error sending power restore email to {user.email}: {str(e)}")
    
    def _send_production_without_power_email(self, user, device, event):
        """Send production without power email notification"""
        try:
            subject = f"CRITICAL: Production Without Power - Device {device.name}"
            message = f"""
            CRITICAL SYSTEM ALERT
            
            Device: {device.name}
            Factory: {device.factory.name if device.factory else 'Unknown'}
            Time: {event.created_at}
            AIN1 Value: {event.ain1_value}
            
            CRITICAL ISSUE: The device is showing production activity without power.
            This indicates a serious system malfunction that requires immediate attention.
            
            Possible causes:
            - Sensor malfunction
            - Data corruption
            - System tampering
            - Hardware failure
            
            Please investigate immediately.
            
            This is an automated alert from the Mill Management System.
            """
            
            # Send email
            success = self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                message=message,
                email_type='system_alert'
            )
            
            if success:
                event.email_sent = True
                event.save()
                
                # Log email
                EmailHistory.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    email_type='system_alert',
                    status='sent'
                )
                
        except Exception as e:
            logger.error(f"Error sending production without power email to {user.email}: {str(e)}")
    
    def get_device_power_status(self, device):
        """Get current power status for a device"""
        try:
            return DevicePowerStatus.objects.get(device=device)
        except DevicePowerStatus.DoesNotExist:
            return None
    
    def get_active_power_events(self, device=None):
        """Get active (unresolved) power events"""
        try:
            queryset = PowerEvent.objects.filter(is_resolved=False)
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
            
            # Get power status summary
            total_devices = Device.objects.count()
            devices_with_power = DevicePowerStatus.objects.filter(has_power=True).count()
            devices_without_power = DevicePowerStatus.objects.filter(has_power=False).count()
            
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