from django.core.management.base import BaseCommand
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test direct connection to both databases'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Testing direct connections...")
            
            # Test testdb connection
            self.stdout.write("\n=== TESTDB CONNECTION ===")
            try:
                conn = psycopg2.connect(
                    dbname=os.getenv('DB_NAME', 'testdb'),
                    user=os.getenv('DB_USER', 'testuser'),
                    password=os.getenv('DB_PASSWORD', 'testpassword'),
                    host=os.getenv('DB_HOST', '45.154.238.114'),
                    port=os.getenv('DB_PORT', '5433')
                )
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"✓ Connected to: {db_info[0]}, User: {db_info[1]}")
                    
                    # Check mill_device table
                    cursor.execute("SELECT COUNT(*) FROM mill_device")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"  mill_device records: {count}")
                    
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Testdb connection failed: {str(e)}"))
            
            # Test counterdb connection
            self.stdout.write("\n=== COUNTERDB CONNECTION ===")
            try:
                conn = psycopg2.connect(
                    dbname='counter',
                    user='root',
                    password='testpassword',
                    host=os.getenv('DB_HOST', '45.154.238.114'),
                    port='5432'
                )
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"✓ Connected to: {db_info[0]}, User: {db_info[1]}")
                    
                    # Check mqtt_data table
                    cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"  mqtt_data records: {count}")
                    
                    # Show sample device IDs
                    cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id LIMIT 5")
                    device_ids = cursor.fetchall()
                    self.stdout.write(f"  Sample device IDs:")
                    for device_id in device_ids:
                        self.stdout.write(f"    {device_id[0]}")
                    
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Counterdb connection failed: {str(e)}"))
            
            # Show environment variables
            self.stdout.write("\n=== ENVIRONMENT VARIABLES ===")
            self.stdout.write(f"DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
            self.stdout.write(f"DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
            self.stdout.write(f"DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
            self.stdout.write(f"DB_PASSWORD: {os.getenv('DB_PASSWORD', 'NOT SET')}")
            self.stdout.write(f"DB_PORT: {os.getenv('DB_PORT', 'NOT SET')}")
            
            self.stdout.write(self.style.SUCCESS("\nDirect connection test completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in test_direct_connection: {e}") 