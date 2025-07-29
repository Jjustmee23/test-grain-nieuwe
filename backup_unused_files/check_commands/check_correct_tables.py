from django.core.management.base import BaseCommand
from django.db import connections
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check the correct table names in both databases'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Checking correct table names...")
            
            # Check testdb for mill_devices
            self.stdout.write("\n=== TESTDB (default) ===")
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"Database: {db_info[0]}, User: {db_info[1]}")
                    
                    # Check for mill_devices table
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name LIKE '%mill%'
                        ORDER BY table_name
                    """)
                    mill_tables = cursor.fetchall()
                    self.stdout.write(f"\nMill tables in testdb:")
                    for table in mill_tables:
                        self.stdout.write(f"  {table[0]}")
                    
                    # Check mill_devices specifically
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mill_devices'")
                    has_mill_devices = cursor.fetchone()[0] > 0
                    if has_mill_devices:
                        self.stdout.write("\n✓ mill_devices table found!")
                        cursor.execute("SELECT COUNT(*) FROM mill_devices")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f"  Records: {count}")
                        
                        # Show sample records
                        cursor.execute("SELECT id, name FROM mill_devices LIMIT 5")
                        samples = cursor.fetchall()
                        self.stdout.write("  Sample records:")
                        for sample in samples:
                            self.stdout.write(f"    ID: {sample[0]}, Name: {sample[1] or 'NO NAME'}")
                    else:
                        self.stdout.write("\n❌ mill_devices table not found!")
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with testdb: {str(e)}"))
            
            # Check counterdb for mqtt_data
            self.stdout.write("\n=== COUNTERDB ===")
            try:
                with connections['counterdb'].cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"Database: {db_info[0]}, User: {db_info[1]}")
                    
                    # Check for mqtt_data table
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name LIKE '%mqtt%'
                        ORDER BY table_name
                    """)
                    mqtt_tables = cursor.fetchall()
                    self.stdout.write(f"\nMQTT tables in counterdb:")
                    for table in mqtt_tables:
                        self.stdout.write(f"  {table[0]}")
                    
                    # Check mqtt_data specifically
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mqtt_data'")
                    has_mqtt_data = cursor.fetchone()[0] > 0
                    if has_mqtt_data:
                        self.stdout.write("\n✓ mqtt_data table found!")
                        cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f"  Records: {count}")
                        
                        # Show sample records
                        cursor.execute("SELECT counter_id, timestamp, ain1_value, counter_1, mobile_signal FROM mqtt_data ORDER BY timestamp DESC LIMIT 3")
                        samples = cursor.fetchall()
                        self.stdout.write("  Sample records:")
                        for sample in samples:
                            self.stdout.write(f"    Device: {sample[0]}, Time: {sample[1]}, AIN1: {sample[2]}, Counter1: {sample[3]}, Signal: {sample[4]}")
                    else:
                        self.stdout.write("\n❌ mqtt_data table not found!")
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with counterdb: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("\nTable check completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in check_correct_tables: {e}") 