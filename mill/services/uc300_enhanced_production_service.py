from django.utils import timezone
from django.db import connections, transaction
from datetime import datetime, timedelta, date
from mill.models import Device, ProductionData, UC300PilotStatus, CounterResetLog
import logging
from django.db import models

logger = logging.getLogger(__name__)

class UC300EnhancedProductionService:
    """
    Enhanced Production Calculation Service with UC300 Reset Logic Support
    
    Handles both:
    1. Legacy devices: Difference-based calculation with gap handling
    2. UC300 devices: Reset-based calculation with direct counter values
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_uc300_device(self, device):
        """Check if device is part of UC300 pilot program"""
        try:
            pilot_status = UC300PilotStatus.objects.get(device=device)
            return pilot_status.is_pilot_enabled and pilot_status.use_reset_logic
        except UC300PilotStatus.DoesNotExist:
            return False
    
    def calculate_daily_production_uc300(self, device, target_date=None):
        """
        Calculate daily production for UC300 devices using reset logic
        Production = Counter value at time of reset
        """
        if target_date is None:
            target_date = timezone.now().date()
        
        try:
            # Find reset log for the target date
            reset_log = CounterResetLog.objects.filter(
                device=device,
                reset_timestamp__date=target_date,
                reset_successful=True
            ).order_by('-reset_timestamp').first()
            
            if reset_log:
                # Use counter value before reset as daily production
                counter_field = f"{device.selected_counter}_before"
                daily_production = getattr(reset_log, counter_field, 0) or 0
                
                self.logger.info(f"UC300 Device {device.id}: Daily production from reset log = {daily_production}")
                return daily_production
            else:
                # No reset found - check if it's today and get current counter
                if target_date == timezone.now().date():
                    current_counter = self.get_current_counter_value(device)
                    self.logger.info(f"UC300 Device {device.id}: No reset yet today, current counter = {current_counter}")
                    return current_counter
                else:
                    # Past date with no reset = no production
                    self.logger.info(f"UC300 Device {device.id}: No reset log for {target_date}, assuming no production")
                    return 0
                    
        except Exception as e:
            self.logger.error(f"Error calculating UC300 production for device {device.id}: {str(e)}")
            return 0
    
    def calculate_daily_production_legacy(self, device, target_date=None):
        """
        Calculate daily production for legacy devices using difference logic
        """
        if target_date is None:
            target_date = timezone.now().date()
        
        try:
            # Get last counter value from previous day with data
            previous_value = self.get_previous_day_counter_value(device, target_date)
            
            # Get counter value for target date
            current_value = self.get_day_counter_value(device, target_date)
            
            if current_value is not None and previous_value is not None:
                # Calculate difference
                production = current_value - previous_value
                
                # Handle counter reset (production would be negative)
                if production < 0:
                    production = current_value
                
                self.logger.info(f"Legacy Device {device.id}: Production = {current_value} - {previous_value} = {production}")
                return production
            elif current_value is not None:
                # No previous data, use current value
                self.logger.info(f"Legacy Device {device.id}: No previous data, using current value = {current_value}")
                return current_value
            else:
                # No data for this day
                self.logger.info(f"Legacy Device {device.id}: No data for {target_date}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Error calculating legacy production for device {device.id}: {str(e)}")
            return 0
    
    def get_current_counter_value(self, device):
        """Get current counter value from MQTT data"""
        try:
            with connections['counter'].cursor() as cursor:
                cursor.execute(f'''
                    SELECT {device.selected_counter}
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (device.id,))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
        except Exception as e:
            self.logger.error(f"Error getting current counter for device {device.id}: {str(e)}")
            return 0
    
    def get_day_counter_value(self, device, target_date):
        """Get counter value for a specific date"""
        try:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            
            with connections['counter'].cursor() as cursor:
                cursor.execute(f'''
                    SELECT {device.selected_counter}
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    AND timestamp >= %s 
                    AND timestamp <= %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (device.id, start_of_day, end_of_day))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else None
        except Exception as e:
            self.logger.error(f"Error getting day counter for device {device.id} on {target_date}: {str(e)}")
            return None
    
    def get_previous_day_counter_value(self, device, target_date):
        """Get the last counter value from a previous day with data"""
        try:
            # Start from the day before target date
            check_date = target_date - timedelta(days=1)
            
            # Look back up to 30 days for the last known value
            for _ in range(30):
                counter_value = self.get_day_counter_value(device, check_date)
                if counter_value is not None:
                    return counter_value
                check_date -= timedelta(days=1)
            
            return 0  # No previous data found
            
        except Exception as e:
            self.logger.error(f"Error getting previous day counter for device {device.id}: {str(e)}")
            return 0
    
    def calculate_cumulative_values(self, device, target_date=None):
        """
        Calculate weekly, monthly, and yearly cumulative values
        """
        if target_date is None:
            target_date = timezone.now().date()
        
        try:
            # Get start dates for each period
            week_start = target_date - timedelta(days=target_date.weekday())  # Monday
            month_start = target_date.replace(day=1)
            year_start = target_date.replace(month=1, day=1)
            
            # Calculate weekly production (Monday to current date)
            weekly_production = self.sum_daily_production(device, week_start, target_date)
            
            # Calculate monthly production (1st to current date)
            monthly_production = self.sum_daily_production(device, month_start, target_date)
            
            # Calculate yearly production (Jan 1st to current date)
            yearly_production = self.sum_daily_production(device, year_start, target_date)
            
            return {
                'weekly_production': weekly_production,
                'monthly_production': monthly_production,
                'yearly_production': yearly_production
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating cumulative values for device {device.id}: {str(e)}")
            return {
                'weekly_production': 0,
                'monthly_production': 0,
                'yearly_production': 0
            }
    
    def sum_daily_production(self, device, start_date, end_date):
        """Sum daily production values for a date range"""
        try:
            total = 0
            current_date = start_date
            
            while current_date <= end_date:
                # Get existing production data
                production_entry = ProductionData.objects.filter(
                    device=device,
                    created_at__date=current_date
                ).first()
                
                if production_entry:
                    total += production_entry.daily_production
                else:
                    # Calculate on-the-fly if no entry exists
                    if self.is_uc300_device(device):
                        daily_prod = self.calculate_daily_production_uc300(device, current_date)
                    else:
                        daily_prod = self.calculate_daily_production_legacy(device, current_date)
                    total += daily_prod
                
                current_date += timedelta(days=1)
            
            return total
            
        except Exception as e:
            self.logger.error(f"Error summing daily production for device {device.id}: {str(e)}")
            return 0
    
    def calculate_and_store_production(self, device, target_date=None):
        """
        Main method to calculate and store production data for a device
        Handles both UC300 and legacy devices
        """
        if target_date is None:
            target_date = timezone.now().date()
        
        try:
            with transaction.atomic():
                # Determine device type and calculate daily production
                if self.is_uc300_device(device):
                    daily_production = self.calculate_daily_production_uc300(device, target_date)
                    calculation_method = "UC300_reset_based"
                else:
                    daily_production = self.calculate_daily_production_legacy(device, target_date)
                    calculation_method = "legacy_difference_based"
                
                # Calculate cumulative values
                cumulative = self.calculate_cumulative_values(device, target_date)
                
                # Create or update production data
                production_timestamp = timezone.make_aware(
                    datetime.combine(target_date, datetime.max.time()),
                    timezone.get_current_timezone()
                )
                
                production_entry, created = ProductionData.objects.get_or_create(
                    device=device,
                    created_at__date=target_date,
                    defaults={
                        'daily_production': daily_production,
                        'weekly_production': cumulative['weekly_production'],
                        'monthly_production': cumulative['monthly_production'],
                        'yearly_production': cumulative['yearly_production'],
                        'created_at': production_timestamp
                    }
                )
                
                if not created:
                    # Update existing entry
                    production_entry.daily_production = daily_production
                    production_entry.weekly_production = cumulative['weekly_production']
                    production_entry.monthly_production = cumulative['monthly_production']
                    production_entry.yearly_production = cumulative['yearly_production']
                    production_entry.updated_at = timezone.now()
                    production_entry.save()
                
                self.logger.info(f"Production calculated for {device.id} ({calculation_method}): "
                               f"Daily={daily_production}, Weekly={cumulative['weekly_production']}, "
                               f"Monthly={cumulative['monthly_production']}, Yearly={cumulative['yearly_production']}")
                
                return production_entry
                
        except Exception as e:
            self.logger.error(f"Error calculating and storing production for device {device.id}: {str(e)}")
            return None
    
    def process_all_devices(self, target_date=None):
        """Process production calculation for all devices"""
        if target_date is None:
            target_date = timezone.now().date()
        
        processed_count = 0
        error_count = 0
        
        devices = Device.objects.filter(status=True)
        
        for device in devices:
            try:
                result = self.calculate_and_store_production(device, target_date)
                if result:
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                self.logger.error(f"Error processing device {device.id}: {str(e)}")
                error_count += 1
        
        self.logger.info(f"Production calculation complete: {processed_count} devices processed, {error_count} errors")
        
        return {
            'processed': processed_count,
            'errors': error_count,
            'total': devices.count()
        }

# Convenience function for easy access
def get_uc300_production_service():
    """Get instance of UC300EnhancedProductionService"""
    return UC300EnhancedProductionService() 