# Importing all view functions from the modular view files
from .views.dashboard_views import index, view_statistics
from .views.auth_views import register, profile
from .views.device_views import get_devices, manage_devices, add_device, remove_device, toggle_device_status
from .views.factory_views import manage_factory, get_factory_status
from django.contrib.auth.views import LoginView


# You can add any additional shared utilities here if needed
