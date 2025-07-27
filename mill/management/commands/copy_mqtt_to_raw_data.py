from django.core.management.base import BaseCommand
from django.db import connections
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Copy mqtt_data table to raw_data table in testdb database'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
        parser.add_argument('--drop-existing', action='store_true', help='Drop existing raw_data table if it exists')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        drop_existing = options.get('drop_existing')
        self.stdout.write(self.style.SUCCESS('=== COPY MQTT_DATA TO RAW_DATA IN TESTDB ==='))
        
        # Use counter database for reading mqtt_data and testdb for creating raw_data
        with connections['counter'].cursor() as counter_cursor:
            with connections['default'].cursor() as testdb_cursor:
                try:
                    # 1. Check if mqtt_data exists in counter database
                    counter_cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'mqtt_data'
                        );
                    """)
                    mqtt_exists = counter_cursor.fetchone()[0]

                    if not mqtt_exists:
                        self.stdout.write(self.style.ERROR("mqtt_data table does not exist in counter database!"))
                        return

                    self.stdout.write("✓ mqtt_data table exists in counter database")

                    # 2. Get mqtt_data table structure
                    counter_cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = 'mqtt_data' 
                        ORDER BY ordinal_position;
                    """)
                    columns = counter_cursor.fetchall()

                    self.stdout.write(f"✓ Found {len(columns)} columns in mqtt_data")

                    # 3. Check if raw_data exists in testdb
                    testdb_cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'raw_data'
                        );
                    """)
                    raw_exists = testdb_cursor.fetchone()[0]

                    if raw_exists:
                        if drop_existing:
                            if not dry_run:
                                testdb_cursor.execute("DROP TABLE raw_data;")
                                self.stdout.write("✓ Dropped existing raw_data table in testdb")
                            else:
                                self.stdout.write("Would drop existing raw_data table in testdb")
                        else:
                            self.stdout.write(self.style.WARNING("raw_data table already exists in testdb. Use --drop-existing to replace it."))
                            return

                    if not dry_run:
                        # 4. Build CREATE TABLE statement dynamically
                        create_table_sql = "CREATE TABLE raw_data (\n"
                        column_definitions = []
                        
                        for column in columns:
                            col_name, data_type, is_nullable, col_default = column
                            
                            # Map data types if needed
                            if data_type == 'character varying':
                                data_type = 'VARCHAR'
                            elif data_type == 'integer':
                                data_type = 'INTEGER'
                            elif data_type == 'double precision':
                                data_type = 'DOUBLE PRECISION'
                            elif data_type == 'timestamp without time zone':
                                data_type = 'TIMESTAMP'
                            
                            # Build column definition
                            col_def = f"    {col_name} {data_type}"
                            
                            if is_nullable == 'NO':
                                col_def += " NOT NULL"
                            
                            # Handle default values, especially sequences
                            if col_default:
                                if 'nextval' in col_default:
                                    # For sequence defaults, just use SERIAL or remove default
                                    if col_name == 'id':
                                        col_def = f"    {col_name} SERIAL PRIMARY KEY"
                                    else:
                                        col_def = f"    {col_name} {data_type}"
                                        if is_nullable == 'NO':
                                            col_def += " NOT NULL"
                                else:
                                    col_def += f" DEFAULT {col_default}"
                            
                            column_definitions.append(col_def)
                        
                        create_table_sql += ",\n".join(column_definitions)
                        create_table_sql += "\n);"

                        # 5. Create raw_data table in testdb
                        testdb_cursor.execute(create_table_sql)
                        self.stdout.write("✓ Created raw_data table in testdb")

                        # 6. Copy data from counter to testdb
                        counter_cursor.execute("SELECT COUNT(*) FROM mqtt_data;")
                        mqtt_count = counter_cursor.fetchone()[0]
                        self.stdout.write(f"✓ Found {mqtt_count} records in mqtt_data table")

                        if mqtt_count > 0:
                            # Copy data in batches to avoid memory issues
                            batch_size = 1000
                            total_copied = 0
                            
                            # Get column names for INSERT
                            column_names = [col[0] for col in columns]
                            placeholders = ', '.join(['%s'] * len(column_names))
                            column_names_str = ', '.join(column_names)
                            
                            insert_sql = f"INSERT INTO raw_data ({column_names_str}) VALUES ({placeholders})"
                            
                            # Copy in batches
                            for offset in range(0, mqtt_count, batch_size):
                                counter_cursor.execute("""
                                    SELECT * FROM mqtt_data 
                                    ORDER BY id 
                                    LIMIT %s OFFSET %s;
                                """, [batch_size, offset])
                                
                                batch_records = counter_cursor.fetchall()
                                if batch_records:
                                    testdb_cursor.executemany(insert_sql, batch_records)
                                    total_copied += len(batch_records)
                                    self.stdout.write(f"✓ Copied batch {offset//batch_size + 1}: {len(batch_records)} records (Total: {total_copied}/{mqtt_count})")
                            
                            self.stdout.write(f"✓ Successfully copied {total_copied} records to raw_data table in testdb")

                        # 7. Copy indexes from mqtt_data to raw_data
                        counter_cursor.execute("""
                            SELECT indexname, indexdef 
                            FROM pg_indexes 
                            WHERE tablename = 'mqtt_data';
                        """)
                        indexes = counter_cursor.fetchall()

                        for index_name, index_def in indexes:
                            # Modify index definition for raw_data table
                            new_index_def = index_def.replace('mqtt_data', 'raw_data')
                            new_index_name = index_name.replace('mqtt_data', 'raw_data')
                            
                            try:
                                testdb_cursor.execute(new_index_def)
                                self.stdout.write(f"✓ Created index: {new_index_name}")
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"⚠ Could not create index {new_index_name}: {str(e)}"))

                    else:
                        self.stdout.write("DRY RUN - Would create raw_data table in testdb and copy data")

                    # 8. Verify the copy
                    if not dry_run:
                        testdb_cursor.execute("SELECT COUNT(*) FROM raw_data;")
                        raw_count = testdb_cursor.fetchone()[0]
                        
                        if raw_count == mqtt_count:
                            self.stdout.write(
                                self.style.SUCCESS(f"✓ SUCCESS: raw_data table in testdb has {raw_count} records (same as mqtt_data)")
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"⚠ WARNING: Count mismatch! mqtt_data: {mqtt_count}, raw_data: {raw_count}")
                            )

                        # 9. Show sample data
                        testdb_cursor.execute("""
                            SELECT id, counter_id, timestamp, counter_1, counter_2, counter_3, counter_4 
                            FROM raw_data 
                            ORDER BY id DESC 
                            LIMIT 3;
                        """)
                        sample_records = testdb_cursor.fetchall()
                        
                        self.stdout.write("\nSample records in raw_data (testdb):")
                        for record in sample_records:
                            self.stdout.write(f"  ID {record[0]}: {record[1]} - {record[2]} - C1:{record[3]} C2:{record[4]} C3:{record[5]} C4:{record[6]}")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
                    if not dry_run:
                        connections['default'].rollback()

        self.stdout.write(self.style.SUCCESS('\n=== COPY COMPLETE ===')) 