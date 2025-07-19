from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from functools import wraps
from mill.models import City, Factory
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# Existing time and status checking functions
def check_factory_status(counter_data):
    if counter_data.exists():
        last_entry = counter_data.latest('created_at')
        if timezone.now() - last_entry.created_at < timezone.timedelta(minutes=30):
            return True
    return False

def calculate_start_time(counter_data):
    if counter_data.exists():
        return counter_data.first().created_at.time()
    return 'N/A'

def calculate_stop_time(counter_data, factory_status):
    if factory_status:
        return 'Working'
    if counter_data.exists():
        return counter_data.latest('created_at').created_at.time()
    return 'N/A'

def admin_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            if is_admin(request.user) or is_super_admin(request.user):
                return function(request, *args, **kwargs)
            else:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')  # Redirect to dashboard
        return redirect('login')  # Redirect to login if not authenticated
    return wrap


from datetime import date, timedelta

def superadmin_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            if is_super_admin(request.user):
                return function(request, *args, **kwargs)
            else:
                messages.error(request, "This page requires super admin privileges.")
                return redirect('dashboard')  # Redirect to dashboard
        return redirect('login')  # Redirect to login if not authenticated
    return wrap

def is_super_admin(user):
    return user.is_superuser or user.groups.filter(name='Superadmin').exists()

def is_admin(user): 
    return user.is_superuser or user.groups.filter(name='Admin').exists()

def is_public_user(user):
    return user.groups.filter(name='Public').exists()

# Access control functions
def is_allowed_factory(request, factory_id):
    factory = get_object_or_404(Factory, id=factory_id)
    if is_super_admin(request.user) or is_admin(request.user):
        return factory
    if request.user.userprofile.allowed_factories.filter(id=factory.id).exists():
        return factory
    return None
    
def is_allowed_city(request, city_id):
    city = get_object_or_404(City, id=city_id)
    if is_super_admin(request.user):
        return city
    if request.user.userprofile.allowed_cities.filter(id=city.id).exists():
        return city
    return None

def allowed_cities(request):
    if is_super_admin(request.user):
        return City.objects.all()
    return request.user.userprofile.allowed_cities.all()

def allowed_factories(request):
    if is_super_admin(request.user):
        return Factory.objects.all()
    return Factory.objects.filter(id__in=request.user.userprofile.allowed_factories.all())


# Email notification function
def send_notification_email(user, notification):
    subject = f"New Notification: {notification.category.name}"
    message = f"""
    {notification.message}
    View details: {notification.link or ''}
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )