import psycopg2
import logging
from django.utils import timezone
from datetime import datetime, timedelta
from mill.models import Device, RawData, DevicePowerStatus
from mill.services.power_management_service import PowerManagementService

logger = logging.getLogger(__name__)

class CounterSyncService:
    """Service to sync data from counter database to testdb"""
    
    def __init__(self):
        self.counter_db_settings = {
            "dbname": "counter",
            "user": "root",
            "password": "testpassword",
            "host": "45.154.238.114",
            "port": "5432",
        }
        self.power_service = PowerManagementService()
    
    def sync_latest_data(self, device_id=None):
        """Sync latest data from counter database to testdb"""
        try:
            conn = psycopg2.connect(**self.counter_db_settings)
            cursor = conn.cursor()
            
            # Get latest data for each counter_id
            if device_id:
                # Sync specific device
                cursor.execute("""
                    SELECT 
                        *,
                        ROW_NUMBER() OVER (PARTITION BY counter_id ORDER BY timestamp DESC) AS rn
                    FROM 
                        mqtt_data
                    WHERE 
                        counter_id = %s
                """, (device_id,))
            else:
                # Sync all devices
                cursor.execute("""
                    WITH RankedData AS (
                        SELECT 
                            *,
                            ROW_NUMBER() OVER (PARTITION BY counter_id ORDER BY timestamp DESC) AS rn
                        FROM 
                            mqtt_data
                    )
                    SELECT 
                        *
                    FROM 
                        RankedData
                    WHERE 
                        rn = 1
                    ORDER BY 
                        timestamp DESC
                """)
            
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            synced_count = 0
            skipped_count = 0
            
            for row in data:
                try:
                    # Parse the row data (adjust column indices based on actual schema)
                    # Assuming columns: id, counter_id, timestamp, mobile_signal, dout_enabled, dout, di_mode, din, 
                    # counter_1, counter_2, counter_3, counter_4, ain_mode, ain1_value, ain2_value, ain3_value, 
                    # ain4_value, ain5_value, ain6_value, ain7_value, ain8_value, start_flag, type, length, version, end_flag
                    
                    counter_id = row[1]  # counter_id column
                    timestamp_str = row[2]  # timestamp column
                    mobile_signal = row[3]
                    dout_enabled = row[4]
                    dout = row[5]
                    di_mode = row[6]
                    din = row[7]
                    counter_1 = row[8]
                    counter_2 = row[9]
                    counter_3 = row[10]
                    counter_4 = row[11]
                    ain_mode = row[12]
                    ain1_value = row[13]  # Power value
                    ain2_value = row[14]
                    ain3_value = row[15]
                    ain4_value = row[16]
                    ain5_value = row[17]
                    ain6_value = row[18]
                    ain7_value = row[19]
                    ain8_value = row[20]
                    start_flag = row[21]
                    type_val = row[22]
                    length_val = row[23]
                    version_val = row[24]
                    end_flag = row[25]
                    
                    # Parse timestamp and validate
                    if isinstance(timestamp_str, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except ValueError:
                            # Skip invalid timestamp format
                            logger.warning(f"Invalid timestamp format for device {counter_id}: {timestamp_str}")
                            skipped_count += 1
                            continue
                    else:
                        timestamp = timestamp_str
                    
                    # Validate timestamp is logical (not too old or future)
                    current_year = timezone.now().year
                    if timestamp.year < 2020 or timestamp.year > current_year + 1:
                        logger.warning(f"Illogical timestamp for device {counter_id}: {timestamp} (year: {timestamp.year})")
                        skipped_count += 1
                        continue
                    
                    # Make timestamp timezone-aware if it's naive
                    if timezone.is_naive(timestamp):
                        timestamp = timezone.make_aware(timestamp)
                    
                    # Get or create device
                    device, created = Device.objects.get_or_create(
                        id=counter_id,
                        defaults={'name': f'Device {counter_id}', 'status': True}
                    )
                    
                    # Check if we already have this data (avoid duplicates)
                    existing_data = RawData.objects.filter(
                        device=device,
                        timestamp=timestamp,
                        ain1_value=ain1_value
                    ).first()
                    
                    if existing_data:
                        logger.debug(f"Data already exists for device {counter_id} at {timestamp}")
                        continue
                    
                    # Create RawData entry
                    raw_data = RawData.objects.create(
                        device=device,
                        timestamp=timestamp,
                        mobile_signal=mobile_signal,
                        dout_enabled=dout_enabled,
                        dout=dout,
                        di_mode=di_mode,
                        din=din,
                        counter_1=counter_1,
                        counter_2=counter_2,
                        counter_3=counter_3,
                        counter_4=counter_4,
                        ain_mode=ain_mode,
                        ain1_value=ain1_value,  # Power value
                        ain2_value=ain2_value,
                        ain3_value=ain3_value,
                        ain4_value=ain4_value,
                        ain5_value=ain5_value,
                        ain6_value=ain6_value,
                        ain7_value=ain7_value,
                        ain8_value=ain8_value,
                        start_flag=start_flag,
                        type=type_val,
                        length=length_val,
                        version=version_val,
                        end_flag=end_flag
                    )
                    
                    # Process power management
                    self.power_service.process_raw_data(raw_data)
                    
                    synced_count += 1
                    logger.info(f"Synced data for device {counter_id}: ain1_value={ain1_value}")
                    
                except Exception as e:
                    logger.error(f"Error syncing data for row {row}: {str(e)}")
                    continue
            
            logger.info(f"Successfully synced {synced_count} data records from counter database (skipped {skipped_count} invalid timestamps)")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error connecting to counter database: {str(e)}")
            return 0
    
    def sync_historical_data(self, days=7, device_id=None):
        """Sync historical data from counter database to testdb"""
        try:
            conn = psycopg2.connect(**self.counter_db_settings)
            cursor = conn.cursor()
            
            # Calculate date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Get historical data
            if device_id:
                cursor.execute("""
                    SELECT * FROM mqtt_data 
                    WHERE counter_id = %s 
                    AND timestamp >= %s 
                    AND timestamp <= %s
                    ORDER BY timestamp DESC
                """, (device_id, start_date, end_date))
            else:
                cursor.execute("""
                    SELECT * FROM mqtt_data 
                    WHERE timestamp >= %s 
                    AND timestamp <= %s
                    ORDER BY timestamp DESC
                """, (start_date, end_date))
            
            data = cursor.fetchall()
            cursor.close()
            conn.close()
            
            synced_count = 0
            skipped_count = 0
            
            for row in data:
                try:
                    # Parse the row data (same as above)
                    counter_id = row[1]
                    timestamp_str = row[2]
                    mobile_signal = row[3]
                    dout_enabled = row[4]
                    dout = row[5]
                    di_mode = row[6]
                    din = row[7]
                    counter_1 = row[8]
                    counter_2 = row[9]
                    counter_3 = row[10]
                    counter_4 = row[11]
                    ain_mode = row[12]
                    ain1_value = row[13]  # Power value
                    ain2_value = row[14]
                    ain3_value = row[15]
                    ain4_value = row[16]
                    ain5_value = row[17]
                    ain6_value = row[18]
                    ain7_value = row[19]
                    ain8_value = row[20]
                    start_flag = row[21]
                    type_val = row[22]
                    length_val = row[23]
                    version_val = row[24]
                    end_flag = row[25]
                    
                    # Parse timestamp and validate
                    if isinstance(timestamp_str, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except ValueError:
                            # Skip invalid timestamp format
                            logger.warning(f"Invalid timestamp format for device {counter_id}: {timestamp_str}")
                            skipped_count += 1
                            continue
                    else:
                        timestamp = timestamp_str
                    
                    # Validate timestamp is logical (not too old or future)
                    current_year = timezone.now().year
                    if timestamp.year < 2020 or timestamp.year > current_year + 1:
                        logger.warning(f"Illogical timestamp for device {counter_id}: {timestamp} (year: {timestamp.year})")
                        skipped_count += 1
                        continue
                    
                    # Make timestamp timezone-aware if it's naive
                    if timezone.is_naive(timestamp):
                        timestamp = timezone.make_aware(timestamp)
                    
                    # Get or create device
                    device, created = Device.objects.get_or_create(
                        id=counter_id,
                        defaults={'name': f'Device {counter_id}', 'status': True}
                    )
                    
                    # Check if we already have this data
                    existing_data = RawData.objects.filter(
                        device=device,
                        timestamp=timestamp,
                        ain1_value=ain1_value
                    ).first()
                    
                    if existing_data:
                        continue
                    
                    # Create RawData entry
                    raw_data = RawData.objects.create(
                        device=device,
                        timestamp=timestamp,
                        mobile_signal=mobile_signal,
                        dout_enabled=dout_enabled,
                        dout=dout,
                        di_mode=di_mode,
                        din=din,
                        counter_1=counter_1,
                        counter_2=counter_2,
                        counter_3=counter_3,
                        counter_4=counter_4,
                        ain_mode=ain_mode,
                        ain1_value=ain1_value,  # Power value
                        ain2_value=ain2_value,
                        ain3_value=ain3_value,
                        ain4_value=ain4_value,
                        ain5_value=ain5_value,
                        ain6_value=ain6_value,
                        ain7_value=ain7_value,
                        ain8_value=ain8_value,
                        start_flag=start_flag,
                        type=type_val,
                        length=length_val,
                        version=version_val,
                        end_flag=end_flag
                    )
                    
                    synced_count += 1
                    
                except Exception as e:
                    logger.error(f"Error syncing historical data for row {row}: {str(e)}")
                    continue
            
            logger.info(f"Successfully synced {synced_count} historical data records from counter database (skipped {skipped_count} invalid timestamps)")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error connecting to counter database for historical data: {str(e)}")
            return 0
    
    def update_power_status_from_counter_db(self):
        """Update power status for all devices based on latest data from counter database"""
        try:
            # First sync latest data
            synced_count = self.sync_latest_data()
            
            if synced_count > 0:
                # Then update power status
                updated_count = self.power_service.update_power_status_from_database()
                logger.info(f"Updated power status for {updated_count} devices after syncing from counter database")
                return updated_count
            else:
                logger.info("No new data synced from counter database")
                return 0
                
        except Exception as e:
            logger.error(f"Error updating power status from counter database: {str(e)}")
            return 0
    
    def get_counter_db_status(self):
        """Get status information from counter database"""
        try:
            conn = psycopg2.connect(**self.counter_db_settings)
            cursor = conn.cursor()
            
            # Get total records
            cursor.execute("SELECT COUNT(*) FROM mqtt_data")
            total_records = cursor.fetchone()[0]
            
            # Get latest timestamp
            cursor.execute("SELECT MAX(timestamp) FROM mqtt_data")
            latest_timestamp = cursor.fetchone()[0]
            
            # Get unique counter_ids
            cursor.execute("SELECT COUNT(DISTINCT counter_id) FROM mqtt_data")
            unique_devices = cursor.fetchone()[0]
            
            # Get records from last 24 hours
            yesterday = timezone.now() - timedelta(days=1)
            cursor.execute("SELECT COUNT(*) FROM mqtt_data WHERE timestamp >= %s", (yesterday,))
            recent_records = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'total_records': total_records,
                'latest_timestamp': latest_timestamp,
                'unique_devices': unique_devices,
                'recent_records_24h': recent_records,
                'connection_status': 'connected'
            }
            
        except Exception as e:
            logger.error(f"Error getting counter database status: {str(e)}")
            return {
                'connection_status': 'error',
                'error_message': str(e)
            } 