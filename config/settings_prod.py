from .settings import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME','testdb'),
        'USER': os.getenv('DB_USER','testuser'),
        'PASSWORD': os.getenv('DB_PASSWORD','testpassword'),
        'HOST': os.getenv('DB_HOST', '45.154.238.114'),
        'PORT': os.getenv('DB_PORT', '5433'),
    }
}