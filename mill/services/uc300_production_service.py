"""
🔄 UC300 Production Service - Pilot System
Enhanced production calculation service that supports UC300 reset functionality.
This runs in parallel with the existing system.
"""

import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Optional, Dict, Any, Tuple
from django.utils import timezone
from django.db import models, connections

from mill.models import Device, ProductionData, CounterResetLog, UC300PilotStatus
from mill.services.production_calculation_service import ProductionCalculationService

logger = logging.getLogger(__name__)

class UC300ProductionService(ProductionCalculationService):
    """
    Enhanced production service that supports UC300 reset functionality.
    Inherits from the original service and adds reset-aware calculations.
    """
    
    def __init__(self):
        super().__init__()
        self.service_name = "UC300 Reset-Aware Production Service"
        logger.info(f"Initialized {self.service_name}")
    
    def is_device_in_pilot(self, device_id: str) -> bool:
        """Check if device is participating in UC300 reset pilot"""
        try:
            device = Device.objects.filter(id=device_id).first()
            if not device:
                return False
            
            pilot_status = getattr(device, 'pilot_status', None)
            return pilot_status and pilot_status.is_pilot_enabled and pilot_status.use_reset_logic
            
        except Exception as e:
            logger.error(f"Error checking pilot status for device {device_id}: {str(e)}")
            return False
    
    def get_reset_log_today(self, device_id: str) -> Optional[CounterResetLog]:
        """Get reset log for device today"""
        try:
            device = Device.objects.filter(id=device_id).first()
            if not device:
                return None
            
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(hours=23, minutes=59, seconds=59)
            
            return CounterResetLog.objects.filter(
                device=device,
                reset_timestamp__range=[today_start, today_end],
                reset_successful=True
            ).order_by('-reset_timestamp').first()
            
        except Exception as e:
            logger.error(f"Error getting reset log for device {device_id}: {str(e)}")
            return None
    
    def calculate_production_with_reset_awareness(self, device_id: str, current_counter_value: int,
                                                 selected_counter: str) -> int:
        """
        Calculate production with awareness of UC300 resets.
        
        Logic:
        - If device is in pilot and had reset today: production = current_counter_value
        - Otherwise: use original calculation logic
        """
        try:
            # Check if device is in reset pilot
            if not self.is_device_in_pilot(device_id):
                # Use original logic for non-pilot devices
                return self.calculate_daily_production_correctly(device_id, current_counter_value, selected_counter)
            
            # Device is in pilot - check for reset today
            reset_today = self.get_reset_log_today(device_id)
            
            if reset_today:
                # Reset occurred today - production is direct counter value
                daily_production = max(0, current_counter_value)
                logger.info(f"UC300 RESET LOGIC - Device {device_id}: "
                          f"Reset at {reset_today.reset_timestamp.strftime('%H:%M')}, "
                          f"Daily production = {daily_production} (direct counter)")
                return daily_production
            else:
                # No reset today - use difference calculation
                yesterday_value = self.get_previous_day_counter_value(device_id, selected_counter)
                
                if yesterday_value is not None:
                    daily_production = max(0, current_counter_value - yesterday_value)
                    logger.info(f"UC300 DIFF LOGIC - Device {device_id}: "
                              f"{current_counter_value} - {yesterday_value} = {daily_production}")
                else:
                    # No yesterday data - use last known value
                    last_known_value = self.get_last_known_counter_value(device_id, selected_counter)
                    daily_production = max(0, current_counter_value - last_known_value)
                    logger.info(f"UC300 LAST KNOWN LOGIC - Device {device_id}: "
                              f"{current_counter_value} - {last_known_value} = {daily_production}")
                
                return daily_production
                
        except Exception as e:
            logger.error(f"Error in reset-aware production calculation for device {device_id}: {str(e)}")
            # Fallback to original logic
            return self.calculate_daily_production_correctly(device_id, current_counter_value, selected_counter)
    
    def update_device_production_with_reset_awareness(self, device_id: str) -> Dict[str, Any]:
        """
        Update production data for a device with UC300 reset awareness.
        This is the enhanced version of the original method.
        """
        try:
            # Check if device is in pilot
            if not self.is_device_in_pilot(device_id):
                # Use original logic for non-pilot devices
                return self.update_device_production_data(device_id)
            
            logger.info(f"🔄 UC300 RESET-AWARE UPDATE: Processing device {device_id}")
            
            # Get device info
            device = Device.objects.filter(id=device_id).first()
            if not device:
                logger.error(f"Device {device_id} not found")
                return {'success': False, 'error': 'Device not found'}
            
            selected_counter = device.selected_counter
            
            # Get today's counter value
            today_counter_value = self.get_today_counter_value(device_id, selected_counter)
            if today_counter_value is None:
                logger.warning(f"No counter data found for device {device_id} today")
                return {'success': False, 'error': 'No counter data today'}
            
            # Calculate daily production with reset awareness
            daily_production = self.calculate_production_with_reset_awareness(
                device_id, today_counter_value, selected_counter
            )
            
            # Get current date for entry
            entry_date = timezone.now().date()
            
            # Calculate cumulative values
            weekly_production, monthly_production, yearly_production = self.calculate_cumulative_values(
                device_id, daily_production, entry_date
            )
            
            # Insert or update production data
            production_result = self.insert_or_update_production_data(
                device_id=device_id,
                daily_production=daily_production,
                weekly_production=weekly_production,
                monthly_production=monthly_production,
                yearly_production=yearly_production,
                entry_date=entry_date
            )
            
            result = {
                'success': True,
                'device_id': device_id,
                'calculation_method': 'UC300_RESET_AWARE',
                'daily_production': daily_production,
                'weekly_production': weekly_production,
                'monthly_production': monthly_production,
                'yearly_production': yearly_production,
                'reset_today': self.get_reset_log_today(device_id) is not None,
                'production_entry': production_result
            }
            
            logger.info(f"✅ UC300 production update completed for {device_id}: {daily_production}")
            return result
            
        except Exception as e:
            logger.error(f"Error in UC300 production update for device {device_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_all_pilot_devices(self) -> Dict[str, Any]:
        """Update production data for all devices in UC300 pilot"""
        try:
            logger.info("🔄 Starting UC300 pilot devices update")
            
            # Get all pilot devices
            pilot_devices = UC300PilotStatus.objects.filter(
                is_pilot_enabled=True,
                use_reset_logic=True
            ).select_related('device')
            
            if not pilot_devices.exists():
                logger.info("No devices in UC300 pilot")
                return {'success': True, 'message': 'No pilot devices', 'devices_updated': 0}
            
            results = []
            success_count = 0
            error_count = 0
            
            for pilot_status in pilot_devices:
                device_id = pilot_status.device.id
                
                try:
                    result = self.update_device_production_with_reset_awareness(device_id)
                    results.append(result)
                    
                    if result.get('success'):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error updating pilot device {device_id}: {str(e)}")
                    results.append({'success': False, 'device_id': device_id, 'error': str(e)})
                    error_count += 1
            
            summary = {
                'success': True,
                'total_pilot_devices': len(pilot_devices),
                'devices_updated': success_count,
                'errors': error_count,
                'results': results
            }
            
            logger.info(f"✅ UC300 pilot update completed: {success_count} success, {error_count} errors")
            return summary
            
        except Exception as e:
            logger.error(f"Error updating all pilot devices: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_all_production_data_hybrid(self) -> Dict[str, Any]:
        """
        Update production data for ALL devices using hybrid approach:
        - UC300 reset logic for pilot devices
        - Original logic for non-pilot devices
        """
        try:
            logger.info("🔄 Starting HYBRID production update (pilot + original)")
            
            # Update pilot devices with reset awareness
            pilot_results = self.update_all_pilot_devices()
            
            # Update non-pilot devices with original logic
            original_results = self.update_all_production_data()
            
            # Combine results
            hybrid_results = {
                'success': True,
                'update_method': 'HYBRID',
                'pilot_results': pilot_results,
                'original_results': original_results,
                'timestamp': timezone.now().isoformat()
            }
            
            logger.info("✅ HYBRID production update completed")
            return hybrid_results
            
        except Exception as e:
            logger.error(f"Error in hybrid production update: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def enable_device_pilot(self, device_id: str, daily_reset_time: str = "06:00", 
                           notes: str = "") -> bool:
        """
        Enable UC300 reset pilot for a device
        
        Args:
            device_id: Device ID to enable pilot for
            daily_reset_time: Daily reset time (HH:MM format)
            notes: Optional notes
            
        Returns:
            bool: True if pilot enabled successfully
        """
        try:
            device = Device.objects.filter(id=device_id).first()
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
            
            # Parse reset time
            reset_time = None
            if daily_reset_time:
                try:
                    hour, minute = map(int, daily_reset_time.split(':'))
                    reset_time = dt_time(hour, minute)
                except ValueError:
                    logger.error(f"Invalid reset time format: {daily_reset_time}")
                    return False
            
            # Create or update pilot status
            pilot_status, created = UC300PilotStatus.objects.get_or_create(device=device)
            pilot_status.is_pilot_enabled = True
            pilot_status.use_reset_logic = True
            pilot_status.daily_reset_time = reset_time
            pilot_status.pilot_start_date = timezone.now()
            pilot_status.notes = notes
            pilot_status.save()
            
            action = "created" if created else "updated"
            logger.info(f"✅ UC300 pilot {action} for device {device_id} - Reset time: {daily_reset_time}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enabling pilot for device {device_id}: {str(e)}")
            return False
    
    def disable_device_pilot(self, device_id: str) -> bool:
        """
        Disable UC300 reset pilot for a device
        
        Args:
            device_id: Device ID to disable pilot for
            
        Returns:
            bool: True if pilot disabled successfully
        """
        try:
            device = Device.objects.filter(id=device_id).first()
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
            
            pilot_status = getattr(device, 'pilot_status', None)
            if pilot_status:
                pilot_status.is_pilot_enabled = False
                pilot_status.use_reset_logic = False
                pilot_status.save()
                
                logger.info(f"✅ UC300 pilot disabled for device {device_id}")
                return True
            else:
                logger.info(f"Device {device_id} was not in pilot")
                return True
                
        except Exception as e:
            logger.error(f"Error disabling pilot for device {device_id}: {str(e)}")
            return False
    
    def get_pilot_status_summary(self) -> Dict[str, Any]:
        """Get summary of UC300 pilot status"""
        try:
            pilot_devices = UC300PilotStatus.objects.filter(
                is_pilot_enabled=True
            ).select_related('device')
            
            total_devices = Device.objects.count()
            pilot_count = pilot_devices.count()
            
            pilot_list = []
            for pilot_status in pilot_devices:
                pilot_list.append({
                    'device_id': pilot_status.device.id,
                    'device_name': pilot_status.device.name,
                    'pilot_start_date': pilot_status.pilot_start_date,
                    'daily_reset_time': pilot_status.daily_reset_time,
                    'days_in_pilot': pilot_status.days_in_pilot(),
                    'use_reset_logic': pilot_status.use_reset_logic
                })
            
            summary = {
                'total_devices': total_devices,
                'pilot_devices': pilot_count,
                'non_pilot_devices': total_devices - pilot_count,
                'pilot_percentage': round((pilot_count / total_devices) * 100, 1) if total_devices > 0 else 0,
                'pilot_devices_list': pilot_list
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting pilot status summary: {str(e)}")
            return {'error': str(e)}


# Convenience functions for external use
def update_pilot_device(device_id: str) -> Dict[str, Any]:
    """Convenience function to update a single pilot device"""
    service = UC300ProductionService()
    return service.update_device_production_with_reset_awareness(device_id)


def update_all_devices_hybrid() -> Dict[str, Any]:
    """Convenience function to update all devices with hybrid approach"""
    service = UC300ProductionService()
    return service.update_all_production_data_hybrid()


def enable_pilot_for_device(device_id: str, reset_time: str = "06:00") -> bool:
    """Convenience function to enable pilot for a device"""
    service = UC300ProductionService()
    return service.enable_device_pilot(device_id, reset_time)


def get_pilot_summary() -> Dict[str, Any]:
    """Convenience function to get pilot status summary"""
    service = UC300ProductionService()
    return service.get_pilot_status_summary() 