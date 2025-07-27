from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test PostgreSQL database connection and show available tables'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Testing PostgreSQL database connection...")
            
            # Test default database
            with connections['default'].cursor() as cursor:
                self.stdout.write("\n=== DEFAULT DATABASE ===")
                cursor.execute("SELECT current_database(), current_user")
                db_info = cursor.fetchone()
                self.stdout.write(f"Database: {db_info[0]}, User: {db_info[1]}")
                
                # Check tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                self.stdout.write(f"\nTables in default database ({len(tables)}):")
                for table in tables:
                    self.stdout.write(f"  {table[0]}")
            
            # Test mqtt_db database
            with connections['mqtt_db'].cursor() as cursor:
                self.stdout.write("\n=== MQTT DATABASE ===")
                cursor.execute("SELECT current_database(), current_user")
                db_info = cursor.fetchone()
                self.stdout.write(f"Database: {db_info[0]}, User: {db_info[1]}")
                
                # Check tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                self.stdout.write(f"\nTables in mqtt database ({len(tables)}):")
                for table in tables:
                    self.stdout.write(f"  {table[0]}")
                
                # Check if mqtt_data table exists
                if any('mqtt_data' in table[0].lower() for table in tables):
                    self.stdout.write("\n✓ mqtt_data table found!")
                    
                    # Check table structure
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'mqtt_data'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    self.stdout.write("\nMQTT data table structure:")
                    for col in columns:
                        self.stdout.write(f"  {col[0]}: {col[1]}")
                    
                    # Check total records
                    cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                    total_count = cursor.fetchone()[0]
                    self.stdout.write(f"\nTotal records in mqtt_data: {total_count}")
                    
                    # Check unique device IDs
                    cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id")
                    device_ids = cursor.fetchall()
                    self.stdout.write(f"\nUnique device IDs ({len(device_ids)}):")
                    for device_id in device_ids:
                        self.stdout.write(f"  {device_id[0]}")
                    
                    # Check latest records
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
                else:
                    self.stdout.write("\n❌ mqtt_data table not found!")
                    self.stdout.write("Available tables that might contain MQTT data:")
                    for table in tables:
                        if any(keyword in table[0].lower() for keyword in ['mqtt', 'data', 'counter', 'device']):
                            self.stdout.write(f"  {table[0]} (possible MQTT data table)")
            
            self.stdout.write(self.style.SUCCESS("\nPostgreSQL database test completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in test_postgres_connection: {e}") 