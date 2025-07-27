from django.core.management.base import BaseCommand
from django.db import connections
from mill.models import RawDataCounter, Device
from django.db.models import Count, Min, Max, Avg
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyze the raw_data table in counter database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=str,
            help='Analyze only a specific device',
        )
        parser.add_argument(
            '--show-sample',
            action='store_true',
            help='Show sample data records',
        )

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        show_sample = options.get('show_sample')

        self.stdout.write(
            self.style.SUCCESS('=== RAW_DATA TABLE ANALYSIS ===')
        )

        # Use the counter database connection
        with connections['counter'].cursor() as cursor:
            try:
                # 1. Check if raw_data table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'raw_data'
                    );
                """)
                raw_exists = cursor.fetchone()[0]

                if not raw_exists:
                    self.stdout.write(
                        self.style.ERROR("raw_data table does not exist in counter database!")
                    )
                    return

                self.stdout.write("✓ raw_data table exists")

                # 2. Get basic statistics
                cursor.execute("SELECT COUNT(*) FROM raw_data;")
                total_records = cursor.fetchone()[0]
                self.stdout.write(f"✓ Total records: {total_records}")

                # 3. Get unique devices
                cursor.execute("SELECT COUNT(DISTINCT counter_id) FROM raw_data;")
                unique_devices = cursor.fetchone()[0]
                self.stdout.write(f"✓ Unique devices: {unique_devices}")

                # 4. Get date range
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM raw_data;")
                date_range = cursor.fetchone()
                if date_range[0] and date_range[1]:
                    self.stdout.write(f"✓ Date range: {date_range[0]} to {date_range[1]}")

                # 5. Get device list
                cursor.execute("SELECT counter_id, COUNT(*) as record_count FROM raw_data GROUP BY counter_id ORDER BY record_count DESC;")
                devices = cursor.fetchall()
                
                self.stdout.write(f"\n=== DEVICE BREAKDOWN ===")
                for device in devices[:10]:  # Show top 10 devices
                    self.stdout.write(f"  {device[0]}: {device[1]} records")

                if len(devices) > 10:
                    self.stdout.write(f"  ... and {len(devices) - 10} more devices")

                # 6. Analyze specific device if provided
                if device_id:
                    self.stdout.write(f"\n=== ANALYSIS FOR DEVICE {device_id} ===")
                    
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_records,
                            MIN(timestamp) as first_record,
                            MAX(timestamp) as last_record,
                            AVG(counter_1) as avg_counter_1,
                            AVG(counter_2) as avg_counter_2,
                            AVG(counter_3) as avg_counter_3,
                            AVG(counter_4) as avg_counter_4,
                            MAX(counter_1) as max_counter_1,
                            MAX(counter_2) as max_counter_2,
                            MAX(counter_3) as max_counter_3,
                            MAX(counter_4) as max_counter_4
                        FROM raw_data 
                        WHERE counter_id = %s
                    """, [device_id])
                    
                    device_stats = cursor.fetchone()
                    if device_stats:
                        self.stdout.write(f"  Total records: {device_stats[0]}")
                        self.stdout.write(f"  First record: {device_stats[1]}")
                        self.stdout.write(f"  Last record: {device_stats[2]}")
                        self.stdout.write(f"  Counter 1 - Avg: {device_stats[3]:.2f}, Max: {device_stats[7]}")
                        self.stdout.write(f"  Counter 2 - Avg: {device_stats[4]:.2f}, Max: {device_stats[8]}")
                        self.stdout.write(f"  Counter 3 - Avg: {device_stats[5]:.2f}, Max: {device_stats[9]}")
                        self.stdout.write(f"  Counter 4 - Avg: {device_stats[6]:.2f}, Max: {device_stats[10]}")

                # 7. Show sample data if requested
                if show_sample:
                    self.stdout.write(f"\n=== SAMPLE DATA ===")
                    cursor.execute("SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 5;")
                    sample_data = cursor.fetchall()
                    
                    for i, row in enumerate(sample_data, 1):
                        self.stdout.write(f"  Record {i}:")
                        self.stdout.write(f"    ID: {row[0]}")
                        self.stdout.write(f"    Device: {row[1]}")
                        self.stdout.write(f"    Timestamp: {row[2]}")
                        self.stdout.write(f"    Counter 1: {row[8]}")
                        self.stdout.write(f"    Counter 2: {row[9]}")
                        self.stdout.write(f"    Counter 3: {row[10]}")
                        self.stdout.write(f"    Counter 4: {row[11]}")
                        self.stdout.write("")

                # 8. Test Django model
                self.stdout.write(f"\n=== DJANGO MODEL TEST ===")
                try:
                    # Test using Django model
                    latest_record = RawDataCounter.objects.using('counter').order_by('-timestamp').first()
                    if latest_record:
                        self.stdout.write(f"✓ Django model works - Latest record: {latest_record}")
                        
                        # Test device-specific query
                        if device_id:
                            device_records = RawDataCounter.objects.using('counter').filter(counter_id=device_id).count()
                            self.stdout.write(f"✓ Device {device_id} has {device_records} records via Django model")
                    else:
                        self.stdout.write("⚠ No records found via Django model")
                        
                except Exception as e:
                    self.stdout.write(f"✗ Django model error: {e}")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS('\n=== ANALYSIS COMPLETE ===')
        ) 