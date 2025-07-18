#!/usr/bin/env python
"""
Start Django application without running migrations
This script starts the Django development server without making any
database structure changes to preserve the existing PostgreSQL database.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Start Django without migrations"""
    # Set Django settings to production (with disabled migrations)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_prod')
    
    # Disable migrations globally
    os.environ['DJANGO_DISABLE_MIGRATIONS'] = 'True'
    
    # Override sys.argv to prevent migration commands
    if len(sys.argv) == 1:
        # If no arguments provided, start the server
        sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000']
    elif 'migrate' in sys.argv or 'makemigrations' in sys.argv:
        print("❌ Migration commands are disabled to preserve database structure")
        print("📝 Use the existing database structure only")
        sys.exit(1)
    
    try:
        django.setup()
        execute_from_command_line(sys.argv)
    except Exception as e:
        print(f"❌ Error starting Django: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 