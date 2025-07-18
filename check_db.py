#!/usr/bin/env python
"""
Database connectivity check script
This script checks if we can connect to the PostgreSQL database
without making any structural changes to the database.
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')
django.setup()

def check_database_connection():
    """Check if we can connect to the database without making changes"""
    try:
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database connection successful!")
            print(f"PostgreSQL version: {version[0]}")
            
            # Check if our tables exist (read-only check)
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"📋 Found {len(tables)} tables in database:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("⚠️  No tables found in database")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_django_models():
    """Check if Django can access the models without migrations"""
    try:
        from mill.models import City, Factory, Device
        
        # Try to count records (read-only operations)
        city_count = City.objects.count()
        factory_count = Factory.objects.count()
        device_count = Device.objects.count()
        
        print(f"📊 Model access successful:")
        print(f"   - Cities: {city_count}")
        print(f"   - Factories: {factory_count}")
        print(f"   - Devices: {device_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model access failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking database connectivity...")
    print("=" * 50)
    
    # Check database connection
    db_ok = check_database_connection()
    
    if db_ok:
        print("\n🔍 Checking Django model access...")
        print("=" * 50)
        models_ok = check_django_models()
        
        if models_ok:
            print("\n✅ All checks passed! Database is ready for use.")
            print("📝 Note: No database structure changes will be made.")
        else:
            print("\n⚠️  Model access issues detected.")
            sys.exit(1)
    else:
        print("\n❌ Database connection failed.")
        sys.exit(1) 