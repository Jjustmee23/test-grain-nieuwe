from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test if the monitor data is loading correctly'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Testing monitor data loading...")
            
            # Test mill_device data
            self.stdout.write("\n=== TESTDB.MILL_DEVICE ===")
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT id, name, status FROM mill_device ORDER BY id LIMIT 5")
                mill_devices = cursor.fetchall()
                self.stdout.write(f"Sample mill_device records:")
                for device in mill_devices:
                    self.stdout.write(f"  ID: {device[0]}, Name: {device[1]}, Status: {device[2]}")
            
            # Test mqtt_data
            self.stdout.write("\n=== COUNTER.MQTT_DATA ===")
            with connections['counter'].cursor() as cursor:
                # Get latest records
                cursor.execute("""
                    SELECT counter_id, timestamp, mobile_signal, din,
                           counter_1, counter_2, counter_3, counter_4,
                           ain1_value, ain2_value, ain3_value, ain4_value
                    FROM mqtt_data 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                latest_records = cursor.fetchall()
                self.stdout.write(f"Latest mqtt_data records:")
                for record in latest_records:
                    self.stdout.write(f"  Device: {record[0]}, Time: {record[1]}, AIN1: {record[8]}, Counter1: {record[4]}, Signal: {record[2]}")
                
                # Get unique device IDs
                cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id LIMIT 10")
                device_ids = cursor.fetchall()
                self.stdout.write(f"\nSample device IDs from mqtt_data:")
                for device_id in device_ids:
                    self.stdout.write(f"  {device_id[0]}")
            
            # Test combined data (like the view does)
            self.stdout.write("\n=== COMBINED DATA TEST ===")
            
            # Get all devices from mill_device
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT id, name, status FROM mill_device ORDER BY id")
                mill_devices = {row[0]: {'name': row[1], 'status': row[2]} for row in cursor.fetchall()}
            
            # Get all unique device IDs from mqtt_data
            with connections['counter'].cursor() as cursor:
                cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id")
                active_device_ids = [row[0] for row in cursor.fetchall()]
            
            # Combine all devices
            all_device_ids = list(set(list(mill_devices.keys()) + active_device_ids))
            all_device_ids.sort()
            
            self.stdout.write(f"Total combined devices: {len(all_device_ids)}")
            self.stdout.write(f"Devices in mill_device: {len(mill_devices)}")
            self.stdout.write(f"Devices in mqtt_data: {len(active_device_ids)}")
            
            # Test a few devices
            test_devices = all_device_ids[:5]
            for device_id in test_devices:
                device_info = mill_devices.get(device_id, {'name': None, 'status': False})
                
                # Get latest mqtt data for this device
                with connections['counter'].cursor() as cursor:
                    cursor.execute("""
                        SELECT counter_id, timestamp, ain1_value, counter_1, mobile_signal
                        FROM mqtt_data 
                        WHERE counter_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, [device_id])
                    
                    latest_record = cursor.fetchone()
                
                if latest_record:
                    self.stdout.write(f"  Device {device_id}: {device_info['name']} - Active (AIN1: {latest_record[2]}, Counter1: {latest_record[3]})")
                else:
                    self.stdout.write(f"  Device {device_id}: {device_info['name']} - Offline")
            
            self.stdout.write(self.style.SUCCESS("\nMonitor data test completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in test_monitor_data: {e}") 