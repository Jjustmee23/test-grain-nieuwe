from django.utils import timezone
from django.db import connections
from datetime import datetime, timedelta
from mill.models import Device, ProductionData
import logging
from django.db import models

logger = logging.getLogger(__name__)

class ProductionCalculationService:
    """
    Service to calculate and update production data using the original logic
    from the cronjob system with proper gap handling
    """
    
    def get_last_production_date(self, device_id):
        """Get the date of the last production entry for a device"""
        try:
            latest_production = ProductionData.objects.filter(device_id=device_id).order_by('-created_at').first()
            return latest_production.created_at.date() if latest_production else None
        except Exception as e:
            logger.error(f"Error getting last production date for device {device_id}: {str(e)}")
            return None
    
    def get_typical_daily_production(self, device_id):
        """Get typical daily production for a device based on last 30 days"""
        try:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            avg_production = ProductionData.objects.filter(
                device_id=device_id,
                daily_production__gt=0,
                daily_production__lt=1000,  # Exclude outliers
                created_at__gte=thirty_days_ago
            ).aggregate(avg=models.Avg('daily_production'))
            
            return avg_production['avg'] if avg_production['avg'] else 0
        except Exception as e:
            logger.error(f"Error getting typical production for device {device_id}: {str(e)}")
            return 0
    
    def get_last_data_timestamp(self, device_id, selected_counter):
        """Get the timestamp of the last data entry for a device"""
        try:
            with connections['counter'].cursor() as cursor:
                query = f"""
                    SELECT timestamp 
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting last data timestamp for device {device_id}: {str(e)}")
            return None
    
    def get_last_known_counter_value(self, device_id, selected_counter):
        """Get the last known counter value from before today"""
        try:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            with connections['counter'].cursor() as cursor:
                query = f"""
                    SELECT {selected_counter}, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s AND timestamp < %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id, today_start))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.error(f"Error getting last known counter value for device {device_id}: {str(e)}")
            return 0

    def get_previous_day_counter_value(self, device_id, selected_counter):
        """Get the counter value from the previous day that has data"""
        try:
            yesterday_start = (timezone.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = yesterday_start + timedelta(hours=23, minutes=59, seconds=59)
            
            with connections['counter'].cursor() as cursor:
                query = f"""
                    SELECT {selected_counter}, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s AND timestamp BETWEEN %s AND %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id, yesterday_start, yesterday_end))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else None
        except Exception as e:
            logger.error(f"Error getting yesterday counter value for device {device_id}: {str(e)}")
            return None

    def calculate_daily_production_correctly(self, device_id, today_value, selected_counter):
        """
        Calculate daily production correctly:
        - If both today and yesterday have data: daily = today - yesterday
        - If today has data but yesterday doesn't: daily = today - last_known_value
        - If today has no data: daily = 0
        """
        try:
            # First try to get yesterday's counter value
            yesterday_value = self.get_previous_day_counter_value(device_id, selected_counter)
            
            if yesterday_value is not None:
                # Both today and yesterday have data
                daily_production = max(0, today_value - yesterday_value)
                logger.info(f"Device {device_id}: Yesterday {yesterday_value} → Today {today_value} = Daily: {daily_production}")
            else:
                # No yesterday data, get last known value before today
                last_known_value = self.get_last_known_counter_value(device_id, selected_counter)
                daily_production = max(0, today_value - last_known_value)
                logger.info(f"Device {device_id}: Last known {last_known_value} → Today {today_value} = Daily: {daily_production}")
            
            return daily_production
            
        except Exception as e:
            logger.error(f"Error calculating daily production for device {device_id}: {str(e)}")
            return 0

    def calculate_cumulative_values(self, device_id, daily_production, entry_date):
        """Calculate weekly, monthly, yearly cumulative values"""
        try:
            # Get start dates for each period
            monday_of_week = entry_date - timedelta(days=entry_date.weekday())
            first_of_month = entry_date.replace(day=1)
            first_of_year = entry_date.replace(month=1, day=1)
            
            # Calculate weekly production (sum of daily values this week)
            weekly_production = ProductionData.objects.filter(
                device_id=device_id,
                created_at__date__gte=monday_of_week,
                created_at__date__lte=entry_date
            ).aggregate(total=models.Sum('daily_production'))['total'] or 0
            weekly_production += daily_production  # Add today's production
            
            # Calculate monthly production (sum of daily values this month)
            monthly_production = ProductionData.objects.filter(
                device_id=device_id,
                created_at__date__gte=first_of_month,
                created_at__date__lte=entry_date
            ).aggregate(total=models.Sum('daily_production'))['total'] or 0
            monthly_production += daily_production  # Add today's production
            
            # Calculate yearly production (sum of daily values this year)
            yearly_production = ProductionData.objects.filter(
                device_id=device_id,
                created_at__date__gte=first_of_year,
                created_at__date__lte=entry_date
            ).aggregate(total=models.Sum('daily_production'))['total'] or 0
            yearly_production += daily_production  # Add today's production
            
            return weekly_production, monthly_production, yearly_production
            
        except Exception as e:
            logger.error(f"Error calculating cumulative values for device {device_id}: {str(e)}")
            return daily_production, daily_production, daily_production
    
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
            
            # Calculate production correctly using last known counter value
            production_value = self.calculate_daily_production_correctly(
                device.id, today_value, selected_counter
            )
            
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
    
    def backfill_gap_days(self, device_id, start_date, end_date, total_production):
        """
        Backfill production data for gap days by distributing the total production
        across the missing days.
        """
        try:
            gap_days = (end_date - start_date).days
            if gap_days <= 1:
                return
            
            daily_distributed_production = total_production / gap_days
            logger.info(f"Backfilling {gap_days} days for device {device_id} with {daily_distributed_production:.2f} per day")
            
            # Get the last production data before the gap for cumulative calculations
            last_production = ProductionData.objects.filter(
                device_id=device_id, 
                created_at__date__lt=start_date
            ).order_by('-created_at').first()
            
            current_weekly = last_production.weekly_production if last_production else 0
            current_monthly = last_production.monthly_production if last_production else 0
            current_yearly = last_production.yearly_production if last_production else 0
            
            # Create entries for each missing day
            for i in range(1, gap_days):
                gap_date = start_date + timedelta(days=i)
                gap_datetime = timezone.make_aware(
                    datetime.combine(gap_date, datetime.min.time())
                )
                
                monday_of_week = gap_date - timedelta(days=gap_date.weekday())
                
                # Update cumulative values
                current_weekly += daily_distributed_production
                current_monthly += daily_distributed_production
                current_yearly += daily_distributed_production
                
                # Reset weekly/monthly/yearly if crossing boundaries
                if last_production:
                    if last_production.created_at.date() < monday_of_week:
                        current_weekly = daily_distributed_production
                    if last_production.created_at.month != gap_date.month:
                        current_monthly = daily_distributed_production
                    if last_production.created_at.year != gap_date.year:
                        current_yearly = daily_distributed_production
                
                ProductionData.objects.create(
                    device_id=device_id,
                    daily_production=daily_distributed_production,
                    weekly_production=current_weekly,
                    monthly_production=current_monthly,
                    yearly_production=current_yearly,
                    created_at=gap_datetime
                )
                
                logger.info(f"Created backfill entry for device {device_id} on {gap_date}")
                
        except Exception as e:
            logger.error(f"Error backfilling gap days for device {device_id}: {str(e)}")
    
    def insert_or_update_production_data(self, device_id, production_value):
        """Insert or update production data with correct cumulative calculations"""
        try:
            today = timezone.now().date()
            
            # Get the latest production data for this device
            latest_production = ProductionData.objects.filter(device_id=device_id).order_by('-created_at').first()
            
            if latest_production and latest_production.created_at.date() == today:
                # Update today's entry
                latest_production.daily_production = production_value
                
                # Recalculate cumulative values correctly
                weekly_production, monthly_production, yearly_production = self.calculate_cumulative_values(
                    device_id, production_value, today
                )
                
                latest_production.weekly_production = weekly_production
                latest_production.monthly_production = monthly_production
                latest_production.yearly_production = yearly_production
                latest_production.save()
                
                logger.info(f"Updated production data for device {device_id}: daily={production_value}")
            else:
                # Check for gaps and create entries for missing days with 0 production
                if latest_production:
                    last_date = latest_production.created_at.date()
                    days_gap = (today - last_date).days
                    
                    # Create entries for missing days with 0 production
                    if days_gap > 1:
                        logger.info(f"Gap of {days_gap} days detected for device {device_id}. Creating 0-production entries for missing days.")
                        self.create_zero_production_entries(device_id, last_date, today)
                
                # Calculate cumulative values for today
                weekly_production, monthly_production, yearly_production = self.calculate_cumulative_values(
                    device_id, production_value, today
                )
                
                # Create new entry for today
                ProductionData.objects.create(
                    device_id=device_id,
                    daily_production=production_value,
                    weekly_production=weekly_production,
                    monthly_production=monthly_production,
                    yearly_production=yearly_production,
                )
                logger.info(f"Created new production data for device {device_id}: daily={production_value}")
                
        except Exception as e:
            logger.error(f"Error inserting/updating production data for device {device_id}: {str(e)}")
            raise 

    def create_zero_production_entries(self, device_id, start_date, end_date):
        """Create entries with 0 daily production for missing days"""
        try:
            current_date = start_date + timedelta(days=1)
            
            while current_date < end_date:
                # Calculate cumulative values for this missing day (0 production)
                weekly_production, monthly_production, yearly_production = self.calculate_cumulative_values(
                    device_id, 0, current_date
                )
                
                gap_datetime = timezone.make_aware(
                    datetime.combine(current_date, datetime.min.time())
                )
                
                ProductionData.objects.create(
                    device_id=device_id,
                    daily_production=0,
                    weekly_production=weekly_production,
                    monthly_production=monthly_production,
                    yearly_production=yearly_production,
                    created_at=gap_datetime
                )
                
                logger.info(f"Created 0-production entry for device {device_id} on {current_date}")
                current_date += timedelta(days=1)
                
        except Exception as e:
            logger.error(f"Error creating zero production entries for device {device_id}: {str(e)}") 