from django.core.management.base import BaseCommand
from django.db import connections
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check all available databases and their tables'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Checking all available databases...")
            
            # List all database connections
            self.stdout.write(f"\nAvailable database connections: {list(connections.databases.keys())}")
            
            # Try to connect to counterdb even if not in connections
            db_names = list(connections.databases.keys()) + ['counterdb']
            
            for db_name in db_names:
                self.stdout.write(f"\n=== DATABASE: {db_name} ===")
                
                try:
                    with connections[db_name].cursor() as cursor:
                        # Get database info
                        cursor.execute("SELECT current_database(), current_user")
                        db_info = cursor.fetchone()
                        self.stdout.write(f"Database: {db_info[0]}, User: {db_info[1]}")
                        
                        # Get all tables
                        cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public'
                            ORDER BY table_name
                        """)
                        tables = cursor.fetchall()
                        self.stdout.write(f"\nTables in {db_name} ({len(tables)}):")
                        for table in tables:
                            self.stdout.write(f"  {table[0]}")
                        
                        # Check for specific tables we're interested in
                        table_names = [table[0] for table in tables]
                        
                        if 'mill_device' in table_names:
                            self.stdout.write("\n✓ mill_device table found!")
                            cursor.execute("SELECT COUNT(*) FROM mill_device")
                            count = cursor.fetchone()[0]
                            self.stdout.write(f"  Records: {count}")
                            
                            # Show some sample records
                            cursor.execute("SELECT id, name FROM mill_device LIMIT 5")
                            samples = cursor.fetchall()
                            self.stdout.write("  Sample records:")
                            for sample in samples:
                                self.stdout.write(f"    ID: {sample[0]}, Name: {sample[1] or 'NO NAME'}")
                        
                        if 'mqtt_data' in table_names:
                            self.stdout.write("\n✓ mqtt_data table found!")
                            cursor.execute("SELECT COUNT(*) FROM mqtt_data")
                            count = cursor.fetchone()[0]
                            self.stdout.write(f"  Records: {count}")
                            
                            # Show table structure
                            cursor.execute("""
                                SELECT column_name, data_type 
                                FROM information_schema.columns 
                                WHERE table_name = 'mqtt_data'
                                ORDER BY ordinal_position
                            """)
                            columns = cursor.fetchall()
                            self.stdout.write("  Table structure:")
                            for col in columns:
                                self.stdout.write(f"    {col[0]}: {col[1]}")
                            
                            # Show latest records
                            cursor.execute("""
                                SELECT counter_id, timestamp, ain1_value, counter_1, mobile_signal 
                                FROM mqtt_data 
                                ORDER BY timestamp DESC 
                                LIMIT 3
                            """)
                            latest = cursor.fetchall()
                            self.stdout.write("  Latest records:")
                            for record in latest:
                                self.stdout.write(f"    Device: {record[0]}, Time: {record[1]}, AIN1: {record[2]}, Counter1: {record[3]}, Signal: {record[4]}")
                        
                        # Check for any table with 'counter' in the name
                        counter_tables = [t for t in table_names if 'counter' in t.lower()]
                        if counter_tables:
                            self.stdout.write(f"\nTables with 'counter' in name: {counter_tables}")
                        
                        # Check for any table with 'mqtt' in the name
                        mqtt_tables = [t for t in table_names if 'mqtt' in t.lower()]
                        if mqtt_tables:
                            self.stdout.write(f"Tables with 'mqtt' in name: {mqtt_tables}")
                            
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error connecting to {db_name}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("\nDatabase check completed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Error in check_databases: {e}") 