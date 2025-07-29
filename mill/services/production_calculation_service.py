from django.utils import timezone
from django.db import connections
from datetime import datetime, timedelta
from mill.models import Device, ProductionData
import logging

logger = logging.getLogger(__name__)

class ProductionCalculationService:
    """
    Service to calculate and update production data using the original logic
    from the cronjob system
    """
    
    def update_all_production_data(self):
        """Update production data for all devices"""
        try:
            # Get all devices
            devices = Device.objects.all()
            updated_count = 0
            
            for device in devices:
                try:
                    self.update_device_production_data(device)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating production data for device {device.id}: {str(e)}")
                    continue
            
            return f"Updated {updated_count} devices"
            
        except Exception as e:
            logger.error(f"Error in update_all_production_data: {str(e)}")
            raise
    
    def update_device_production_data(self, device):
        """Update production data for a specific device"""
        try:
            # Get the selected counter for this device
            selected_counter = device.selected_counter
            
            # Get today's latest value
            today_value = self.get_today_latest_value(device.id, selected_counter)
            
            # Get yesterday's latest value
            yesterday_value = self.get_yesterday_latest_value(device.id, selected_counter)
            
            # Calculate production (difference between today and yesterday)
            production_value = max(0, today_value - yesterday_value)
            
            # Update or create production data
            self.insert_or_update_production_data(device.id, production_value)
            
            logger.info(f"Updated production data for device {device.id}: {production_value}")
            
        except Exception as e:
            logger.error(f"Error updating device {device.id}: {str(e)}")
            raise
    
    def get_today_latest_value(self, device_id, selected_counter):
        """Get the latest counter value for today"""
        try:
            with connections['counter'].cursor() as cursor:
                today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                query = f"""
                    SELECT {selected_counter}
                    FROM mqtt_data 
                    WHERE counter_id = %s AND timestamp >= %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id, today_start))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.error(f"Error getting today's value for device {device_id}: {str(e)}")
            return 0
    
    def get_yesterday_latest_value(self, device_id, selected_counter):
        """Get the latest counter value for yesterday"""
        try:
            with connections['counter'].cursor() as cursor:
                yesterday_start = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday_end = yesterday_start + timedelta(hours=23, minutes=59, seconds=59)
                
                query = f"""
                    SELECT {selected_counter}
                    FROM mqtt_data 
                    WHERE counter_id = %s AND timestamp BETWEEN %s AND %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id, yesterday_start, yesterday_end))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.error(f"Error getting yesterday's value for device {device_id}: {str(e)}")
            return 0
    
    def insert_or_update_production_data(self, device_id, production_value):
        """Insert or update production data using the original logic"""
        try:
            today = timezone.now().date()
            monday_of_this_week = today - timedelta(days=today.weekday())
            
            # Get the latest production data for this device
            latest_production = ProductionData.objects.filter(device_id=device_id).order_by('-created_at').first()
            
            if latest_production and latest_production.created_at.date() == today:
                # Update today's entry
                latest_production.daily_production = production_value
                latest_production.weekly_production = latest_production.weekly_production - latest_production.daily_production + production_value
                latest_production.monthly_production = latest_production.monthly_production - latest_production.daily_production + production_value
                latest_production.yearly_production = latest_production.yearly_production - latest_production.daily_production + production_value
                latest_production.save()
                logger.info(f"Updated production data for device {device_id}")
            else:
                # Create new entry
                if latest_production:
                    # Calculate cumulative values
                    weekly_production = production_value if latest_production.created_at.date() < monday_of_this_week else latest_production.weekly_production + production_value
                    monthly_production = production_value if latest_production.created_at.month != today.month else latest_production.monthly_production + production_value
                    yearly_production = production_value if latest_production.created_at.year != today.year else latest_production.yearly_production + production_value
                else:
                    # First entry
                    weekly_production = monthly_production = yearly_production = production_value
                
                ProductionData.objects.create(
                    device_id=device_id,
                    daily_production=production_value,
                    weekly_production=weekly_production,
                    monthly_production=monthly_production,
                    yearly_production=yearly_production,
                )
                logger.info(f"Created new production data for device {device_id}")
                
        except Exception as e:
            logger.error(f"Error inserting/updating production data for device {device_id}: {str(e)}")
            raise 