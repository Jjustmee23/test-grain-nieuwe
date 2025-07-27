from django.core.management.base import BaseCommand
from django.db import connections
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Django connections to both databases'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Testing Django connections...")
            
            # List all database connections
            self.stdout.write(f"\nAvailable database connections: {list(connections.databases.keys())}")
            
            # Test default database (testdb)
            self.stdout.write("\n=== TESTDB (default) ===")
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    db_info = cursor.fetchone()
                    self.stdout.write(f"✓ Connected to: {db_info[0]}, User: {db_info[1]}")
                    
                    # Check mill_device table
                    cursor.execute("SELECT COUNT(*) FROM mill_device")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"  mill_device records: {count}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Testdb connection failed: {str(e)}"))
            
            # Test counter database
            self.stdout.write("\n=== COUNTER DATABASE ===")
            try:
                with connections['counter'].cursor() as cursor:
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
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Counter connection failed: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("\nDjango connection test completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in test_django_connections: {e}") 