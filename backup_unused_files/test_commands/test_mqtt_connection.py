from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test MQTT database connection and show available data'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Testing MQTT database connection...")
            
            # Test connection
            with connections['mqtt_db'].cursor() as cursor:
                # Check if table exists
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                self.stdout.write(f"Available tables: {tables}")
                
                # Check mqtt_data table structure
                try:
                    cursor.execute("DESCRIBE mqtt_data")
                    columns = cursor.fetchall()
                    self.stdout.write("\nMQTT data table structure:")
                    for col in columns:
                        self.stdout.write(f"  {col}")
                except Exception as e:
                    self.stdout.write(f"Error describing mqtt_data table: {e}")
                
                # Check total records
                try:
                    cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                    total_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nTotal records in mqtt_data: {total_count}")
                except Exception as e:
                    self.stdout.write(f"Error counting records: {e}")
                
                # Check unique device IDs
                try:
                    cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id")
                    device_ids = cursor.fetchall()
                    self.stdout.write(f"\nUnique device IDs ({len(device_ids)}):")
                    for device_id in device_ids:
                        self.stdout.write(f"  {device_id[0]}")
                except Exception as e:
                    self.stdout.write(f"Error getting device IDs: {e}")
                
                # Check latest records
                try:
                    cursor.execute("""
                        SELECT counter_id, timestamp, ain1_value, counter_1, mobile_signal 
                        FROM mqtt_data 
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    """)
                    latest_records = cursor.fetchall()
                    self.stdout.write(f"\nLatest 5 records:")
                    for record in latest_records:
                        self.stdout.write(f"  Device: {record[0]}, Time: {record[1]}, AIN1: {record[2]}, Counter1: {record[3]}, Signal: {record[4]}")
                except Exception as e:
                    self.stdout.write(f"Error getting latest records: {e}")
                
                # Check if there's any data from today
                try:
                    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    cursor.execute("SELECT COUNT(*) FROM mqtt_data WHERE timestamp >= %s", [today_start])
                    today_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nRecords from today: {today_count}")
                except Exception as e:
                    self.stdout.write(f"Error getting today's records: {e}")
                
            self.stdout.write(self.style.SUCCESS("MQTT database test completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in test_mqtt_connection: {e}") 