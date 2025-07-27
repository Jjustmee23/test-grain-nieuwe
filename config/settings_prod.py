from .settings import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database configuration for existing PostgreSQL database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME','testdb'),
        'USER': os.getenv('DB_USER','testuser'),
        'PASSWORD': os.getenv('DB_PASSWORD','testpassword'),
        'HOST': os.getenv('DB_HOST', '45.154.238.114'),
        'PORT': os.getenv('DB_PORT', '5433'),
    },
    'counter': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'counter',
        'USER': 'root',
        'PASSWORD': 'testpassword',
        'HOST': os.getenv('DB_HOST', '45.154.238.114'),
        'PORT': '5432',
    }
}

# Temporarily enable migrations for schema updates
# MIGRATION_MODULES = {
#     'mill': None,
# }

# Additional settings to prevent database structure changes
# DJANGO_DISABLE_MIGRATIONS = True