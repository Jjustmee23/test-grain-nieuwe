from django.core.management.base import BaseCommand
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyze both databases and their table structures'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Analyzing databases...")
            
            # Analyze testdb.mill_device
            self.stdout.write("\n" + "="*50)
            self.stdout.write("ANALYZING TESTDB.MILL_DEVICE")
            self.stdout.write("="*50)
            
            try:
                conn = psycopg2.connect(
                    dbname=os.getenv('DB_NAME', 'testdb'),
                    user=os.getenv('DB_USER', 'testuser'),
                    password=os.getenv('DB_PASSWORD', 'testpassword'),
                    host=os.getenv('DB_HOST', '45.154.238.114'),
                    port=os.getenv('DB_PORT', '5433')
                )
                
                with conn.cursor() as cursor:
                    # Get table structure
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = 'mill_device'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    self.stdout.write("\nTable structure:")
                    for col in columns:
                        self.stdout.write(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                    
                    # Get total records
                    cursor.execute("SELECT COUNT(*) FROM mill_device")
                    total_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nTotal records: {total_count}")
                    
                    # Get sample records
                    cursor.execute("SELECT * FROM mill_device LIMIT 5")
                    samples = cursor.fetchall()
                    self.stdout.write(f"\nSample records:")
                    for sample in samples:
                        self.stdout.write(f"  {sample}")
                    
                    # Get devices with names vs without names
                    cursor.execute("SELECT COUNT(*) FROM mill_device WHERE name IS NOT NULL AND name != ''")
                    named_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM mill_device WHERE name IS NULL OR name = ''")
                    unnamed_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nNamed devices: {named_count}")
                    self.stdout.write(f"Unnamed devices: {unnamed_count}")
                    
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error analyzing testdb: {str(e)}"))
            
            # Analyze counter.mqtt_data
            self.stdout.write("\n" + "="*50)
            self.stdout.write("ANALYZING COUNTER.MQTT_DATA")
            self.stdout.write("="*50)
            
            try:
                conn = psycopg2.connect(
                    dbname='counter',
                    user='root',
                    password='testpassword',
                    host=os.getenv('DB_HOST', '45.154.238.114'),
                    port='5432'
                )
                
                with conn.cursor() as cursor:
                    # Get table structure
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = 'mqtt_data'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    self.stdout.write("\nTable structure:")
                    for col in columns:
                        self.stdout.write(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                    
                    # Get total records
                    cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                    total_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nTotal records: {total_count}")
                    
                    # Get unique device IDs
                    cursor.execute("SELECT COUNT(DISTINCT counter_id) FROM mqtt_data")
                    unique_devices = cursor.fetchone()[0]
                    self.stdout.write(f"Unique devices: {unique_devices}")
                    
                    # Get sample device IDs
                    cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id LIMIT 10")
                    device_ids = cursor.fetchall()
                    self.stdout.write(f"\nSample device IDs:")
                    for device_id in device_ids:
                        self.stdout.write(f"  {device_id[0]}")
                    
                    # Get latest records
                    cursor.execute("""
                        SELECT counter_id, timestamp, mobile_signal, din,
                               counter_1, counter_2, counter_3, counter_4,
                               ain1_value
                        FROM mqtt_data 
                        ORDER BY timestamp DESC 
                        LIMIT 5
                    """)
                    latest = cursor.fetchall()
                    self.stdout.write(f"\nLatest 5 records:")
                    for record in latest:
                        self.stdout.write(f"  Device: {record[0]}, Time: {record[1]}, AIN1: {record[2]}, Counter1: {record[3]}, Signal: {record[4]}")
                    
                    # Get data from last 5 minutes
                    cursor.execute("""
                        SELECT COUNT(*) FROM mqtt_data 
                        WHERE timestamp >= NOW() - INTERVAL '5 minutes'
                    """)
                    recent_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nRecords in last 5 minutes: {recent_count}")
                    
                    # Get active devices (with data in last 5 minutes)
                    cursor.execute("""
                        SELECT COUNT(DISTINCT counter_id) FROM mqtt_data 
                        WHERE timestamp >= NOW() - INTERVAL '5 minutes'
                    """)
                    active_devices = cursor.fetchone()[0]
                    self.stdout.write(f"Active devices (last 5 min): {active_devices}")
                    
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error analyzing counter: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("\nDatabase analysis completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in analyze_databases: {e}") 