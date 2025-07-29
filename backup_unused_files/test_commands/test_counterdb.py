from django.core.management.base import BaseCommand
from django.db import connections
import psycopg2
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test direct connection to counterdb'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Testing direct connection to counterdb...")
            
            # Test direct connection
            try:
                conn = psycopg2.connect(
                    dbname='counter',
                    user='root',
                    password='testpassword',
                    host='45.154.238.114',
                    port='5432'
                )
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"✓ Connected to: {db_info[0]}, User: {db_info[1]}")
                    
                    # Check tables
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    tables = cursor.fetchall()
                    self.stdout.write(f"\nTables in counterdb ({len(tables)}):")
                    for table in tables:
                        self.stdout.write(f"  {table[0]}")
                    
                    # Check for mqtt_data table
                    if any('mqtt_data' in table[0].lower() for table in tables):
                        self.stdout.write("\n✓ mqtt_data table found!")
                        
                        # Check total records
                        cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                        total_count = cursor.fetchone()[0]
                        self.stdout.write(f"  Total records: {total_count}")
                        
                        # Check unique device IDs
                        cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id LIMIT 10")
                        device_ids = cursor.fetchall()
                        self.stdout.write(f"  Sample device IDs ({len(device_ids)}):")
                        for device_id in device_ids:
                            self.stdout.write(f"    {device_id[0]}")
                        
                        # Check latest records
                        cursor.execute("""
                            SELECT counter_id, timestamp, ain1_value, counter_1, mobile_signal 
                            FROM mqtt_data 
                            ORDER BY timestamp DESC 
                            LIMIT 3
                        """)
                        latest = cursor.fetchall()
                        self.stdout.write(f"\n  Latest 3 records:")
                        for record in latest:
                            self.stdout.write(f"    Device: {record[0]}, Time: {record[1]}, AIN1: {record[2]}, Counter1: {record[3]}, Signal: {record[4]}")
                    else:
                        self.stdout.write("\n❌ mqtt_data table not found!")
                
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Direct connection failed: {str(e)}"))
            
            # Test Django connection
            self.stdout.write("\nTesting Django connection...")
            try:
                with connections['counterdb'].cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"✓ Django connected to: {db_info[0]}, User: {db_info[1]}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Django connection failed: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("\nCounterdb test completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in test_counterdb: {e}") 