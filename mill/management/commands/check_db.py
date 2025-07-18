from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Check database connectivity without making any structural changes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Checking database connectivity...'))
        self.stdout.write('=' * 50)
        
        try:
            # Test the connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Database connection successful!')
                )
                self.stdout.write(f'PostgreSQL version: {version[0]}')
                
                # Check if our tables exist (read-only check)
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                
                if tables:
                    self.stdout.write(f'📋 Found {len(tables)} tables in database:')
                    for table in tables:
                        self.stdout.write(f'   - {table[0]}')
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  No tables found in database')
                    )
                    
                # Check for specific mill tables
                mill_tables = ['mill_city', 'mill_factory', 'mill_device', 'mill_batch']
                existing_mill_tables = [table[0] for table in tables if table[0] in mill_tables]
                
                if existing_mill_tables:
                    self.stdout.write(f'🏭 Found mill tables: {", ".join(existing_mill_tables)}')
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  No mill tables found - this might be a new database')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {e}')
            )
            return
            
        # Try to access Django models (read-only)
        try:
            from mill.models import City, Factory, Device
            
            city_count = City.objects.count()
            factory_count = Factory.objects.count()
            device_count = Device.objects.count()
            
            self.stdout.write(f'📊 Model access successful:')
            self.stdout.write(f'   - Cities: {city_count}')
            self.stdout.write(f'   - Factories: {factory_count}')
            self.stdout.write(f'   - Devices: {device_count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Model access failed: {e}')
            )
            return
            
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✅ All checks passed! Database is ready for use.')
        )
        self.stdout.write('📝 Note: No database structure changes will be made.') 