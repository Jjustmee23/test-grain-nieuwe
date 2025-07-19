#!/usr/bin/env python
"""
Setup Django auth tables without affecting existing mill tables
This script creates only the necessary Django authentication tables
without running any mill-specific migrations.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Setup Django auth tables"""
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')
    
    # Temporarily enable migrations for auth tables only
    os.environ['DJANGO_DISABLE_MIGRATIONS'] = 'False'
    
    try:
        django.setup()
        
        # Run only auth migrations
        print("🔧 Setting up Django auth tables...")
        
        # Create auth_user table
        sys.argv = ['manage.py', 'migrate', 'auth']
        execute_from_command_line(sys.argv)
        
        # Create contenttypes table
        sys.argv = ['manage.py', 'migrate', 'contenttypes']
        execute_from_command_line(sys.argv)
        
        # Create admin table
        sys.argv = ['manage.py', 'migrate', 'admin']
        execute_from_command_line(sys.argv)
        
        # Create sessions table
        sys.argv = ['manage.py', 'migrate', 'sessions']
        execute_from_command_line(sys.argv)
        
        print("✅ Django auth tables created successfully!")
        print("📝 Note: Mill tables were not affected")
             
    except Exception as e:
        print(f"❌ Error setting up auth tables: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
