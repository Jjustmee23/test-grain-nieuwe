from django.core.management.base import BaseCommand
from django.db import connections
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync new data from mqtt_data to raw_data table in testdb'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force-sync-all',
            action='store_true',
            help='Force sync all data (not just new records)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        force_sync_all = options.get('force_sync_all')

        self.stdout.write(
            self.style.SUCCESS('=== SYNC RAW_DATA FROM MQTT_DATA TO TESTDB ===')
        )

        # Use the counter database for reading mqtt_data and testdb for raw_data
        with connections['counter'].cursor() as counter_cursor:
            with connections['default'].cursor() as testdb_cursor:
                try:
                    # 1. Check if mqtt_data table exists in counter database
                    counter_cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'mqtt_data'
                        );
                    """)
                    mqtt_exists = counter_cursor.fetchone()[0]

                    # 2. Check if raw_data table exists in testdb
                    testdb_cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'raw_data'
                        );
                    """)
                    raw_exists = testdb_cursor.fetchone()[0]

                    if not mqtt_exists:
                        self.stdout.write(
                            self.style.ERROR("mqtt_data table does not exist in counter database!")
                        )
                        return

                    if not raw_exists:
                        self.stdout.write(
                            self.style.ERROR("raw_data table does not exist in testdb! Run copy_mqtt_to_raw_data first.")
                        )
                        return

                    self.stdout.write("✓ Both tables exist")

                    # 3. Get the latest timestamp from raw_data in testdb
                    testdb_cursor.execute("SELECT MAX(id) FROM raw_data;")
                    latest_raw_id = testdb_cursor.fetchone()[0] or 0

                    self.stdout.write(f"✓ Latest ID in raw_data (testdb): {latest_raw_id}")

                    # 4. Get count of new records in mqtt_data from counter database
                    if force_sync_all:
                        counter_cursor.execute("SELECT COUNT(*) FROM mqtt_data;")
                        new_records_count = counter_cursor.fetchone()[0]
                        self.stdout.write(f"✓ Force sync all: {new_records_count} records in mqtt_data")
                    else:
                        counter_cursor.execute("SELECT COUNT(*) FROM mqtt_data WHERE id > %s;", [latest_raw_id])
                        new_records_count = counter_cursor.fetchone()[0]
                        self.stdout.write(f"✓ New records in mqtt_data: {new_records_count}")

                    if new_records_count == 0:
                        self.stdout.write(
                            self.style.SUCCESS("✓ No new data to sync")
                        )
                        return

                    # 5. Sync the new data
                    if not dry_run:
                        if force_sync_all:
                            # Clear raw_data and copy all from mqtt_data
                            testdb_cursor.execute("DELETE FROM raw_data;")
                            self.stdout.write("✓ Cleared raw_data table in testdb")
                            
                            # Copy all data from counter to testdb
                            counter_cursor.execute("SELECT * FROM mqtt_data ORDER BY id;")
                            all_records = counter_cursor.fetchall()
                            
                            # Get column names for INSERT
                            counter_cursor.execute("""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = 'mqtt_data' 
                                ORDER BY ordinal_position;
                            """)
                            columns = [col[0] for col in counter_cursor.fetchall()]
                            placeholders = ', '.join(['%s'] * len(columns))
                            column_names = ', '.join(columns)
                            
                            insert_sql = f"INSERT INTO raw_data ({column_names}) VALUES ({placeholders})"
                            testdb_cursor.executemany(insert_sql, all_records)
                            
                            self.stdout.write(f"✓ Copied all {new_records_count} records from counter to testdb")
                        else:
                            # Insert only new records
                            counter_cursor.execute("""
                                SELECT * FROM mqtt_data 
                                WHERE id > %s
                                ORDER BY id;
                            """, [latest_raw_id])
                            new_records = counter_cursor.fetchall()
                            
                            if new_records:
                                # Get column names for INSERT
                                counter_cursor.execute("""
                                    SELECT column_name 
                                    FROM information_schema.columns 
                                    WHERE table_name = 'mqtt_data' 
                                    ORDER BY ordinal_position;
                                """)
                                columns = [col[0] for col in counter_cursor.fetchall()]
                                placeholders = ', '.join(['%s'] * len(columns))
                                column_names = ', '.join(columns)
                                
                                insert_sql = f"INSERT INTO raw_data ({column_names}) VALUES ({placeholders})"
                                testdb_cursor.executemany(insert_sql, new_records)
                                
                                self.stdout.write(f"✓ Synced {new_records_count} new records to testdb")

                        # 6. Verify the sync
                        testdb_cursor.execute("SELECT COUNT(*) FROM raw_data;")
                        raw_count = testdb_cursor.fetchone()[0]
                        
                        counter_cursor.execute("SELECT COUNT(*) FROM mqtt_data;")
                        mqtt_count = counter_cursor.fetchone()[0]
                        
                        if raw_count == mqtt_count:
                            self.stdout.write(
                                self.style.SUCCESS(f"✓ SUCCESS: raw_data in testdb now has {raw_count} records (same as mqtt_data)")
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"⚠ WARNING: Count mismatch! mqtt_data: {mqtt_count}, raw_data: {raw_count}")
                            )

                        # 7. Show latest synced records
                        testdb_cursor.execute("""
                            SELECT id, counter_id, timestamp, counter_1, counter_2, counter_3, counter_4 
                            FROM raw_data 
                            ORDER BY id DESC 
                            LIMIT 5;
                        """)
                        latest_records = testdb_cursor.fetchall()
                        
                        self.stdout.write("\nLatest records in raw_data (testdb):")
                        for record in latest_records:
                            self.stdout.write(f"  ID {record[0]}: {record[1]} - {record[2]} - C1:{record[3]} C2:{record[4]} C3:{record[5]} C4:{record[6]}")

                    else:
                        self.stdout.write(f"DRY RUN - Would sync {new_records_count} records to testdb")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error: {str(e)}")
                    )
                    if not dry_run:
                        # Rollback any changes
                        connections['default'].rollback()

        self.stdout.write(
            self.style.SUCCESS('\n=== SYNC COMPLETE ===')
        ) 