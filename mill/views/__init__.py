from .dashboard_views import index
from .auth_views import *
from .device_views import *
from .factory_views import manage_factory
# from .admin_views import *
from .city_views import manage_city
from .stats_views import view_statistics

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import user_passes_test, login_required
from mill.forms import CustomUserCreationForm, FactoryForm
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
import csv, openpyxl  
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from mill.models import City, Factory, Device, ProductionData 
import logging
from datetime import datetime, time  # Import time class
from django.utils import timezone
from django.db.models import Sum  # Add this import
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

def check_factory_status(counter_data):
    print(counter_data)
    if counter_data.exists():
        last_entry = counter_data.latest('created_at')  # Get the latest entry based on created_at
        print('timezone',timezone.now(),'las_entry',last_entry)
        if timezone.now() - last_entry.created_at < timezone.timedelta(minutes=30):
            print("telling that factory is working");
            return True  # Last entry is less than 30 minutes ago
    return False  # No entries or last entry is older than 30 minutes

#Daily_total for today
def calculate_daily_total_today(selected_counter, counter_data):
    # daily_total = loop counter_data and add value of selected counter to it
    if selected_counter =='counter_1':
        daily_total = sum(counter.counter_1 for counter in counter_data)
    elif selected_counter =='counter_2':
        daily_total = sum(counter.counter_2 for counter in counter_data)
    elif selected_counter =='counter_3':
        daily_total = sum(counter.counter_3 for counter in counter_data)
    elif selected_counter =='counter_4':
        daily_total = sum(counter.counter_4 for counter in counter_data)
    return daily_total


#Daily_total previous days
def calculate_daily_total_previous(device_data):
    return device_data.daily_total

#Calculate start Time
def calculate_start_time(counter_data):
    if counter_data.exists():
        return counter_data.first().created_at.time()  # Return only the time of the first entry
    return 'N/A'  # No entries exist

#Calculate stop Time
def calculate_stop_time(counter_data, factory_status):
    if factory_status:
        return 'Working'  # Factory is currently working
    else:
        if counter_data.exists():
            return counter_data.latest('created_at').created_at.time()  # Return only the time of the last entry
        return 'N/A'  # No entries exist
    
# Aggregate_city Data
def aggregate_city_data(city_data, factory_data):
    print(city_data)
    print(factory_data)
    city_data['daily_total'] = city_data.get('daily_total', 0) + factory_data.daily_total
    city_data['weekly_total'] = city_data.get('weekly_total', 0) + factory_data.weekly_total
    city_data['monthly_total'] = city_data.get('monthly_total', 0) + factory_data.monthly_total
    city_data['yearly_total'] = city_data.get('yearly_total', 0) + factory_data.yearly_total

@login_required
def profile(request):
    return render(request, 'mill/profile.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user to the database
            login(request, user)  # Log in the user after registration
            # Assign the 'user' group to the new user
            user_group = Group.objects.get(name='user')
            user.groups.add(user_group)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'mill/register.html', {'form': form})

def monitor_required(user):
    return user.groups.filter(name='monitor').exists() or user.is_superuser

def super_admin_required(user):
    return user.groups.filter(name='super_admin').exists() or user.is_superuser

def admin_view(request):
    # provide request.user as context
    context = {
        'user': request.user
    }
    return render(request, 'mill/admin.html', context)

from django.utils.translation import get_language
from django.shortcuts import render

def super_admin_view(request):
    current_locale = get_language()  # Gets the current language
    dir = 'rtl' if current_locale == 'ar' else 'ltr'
    return render(request, 'mill/super_admin.html', {'dir': dir, 'lang': current_locale})

# Manage views for users, databases, devices, tables, factory, city, etc.

def manage_databases(request):
    return render(request, 'mill/manage_databases.html')

def manage_tables(request):
    return render(request, 'mill/manage_tables.html')

from datetime import date

def fetch_device_data_for_device(filter):
    # Fetch daily total for the factory
     object_data = ProductionData.objects.filter(
        **filter
    )
     return object_data

def fetch_counter_data_for_device(filter):
     return
    # Fetch daily total for the factory
     object_data = CountersData.objects.filter(
        **filter
    )
     return object_data


def view_tables(request):
    return render(request, 'mill/view_tables.html')

def manage_admin_view(request):
    return render(request, 'mill/manage_admin.html')

def download_factories(request):
    # Logic to generate and serve the Excel file
    return HttpResponse('Excel download logic here')
    
def api_get_available_devices(request):
    """
    Fetch devices not currently linked to any factory.
    """
    linked_devices = Device.objects.filter(factory__isnull=False)
    available_devices = Device.objects.exclude(id__in=linked_devices.values_list('id', flat=True))
    data = {"devices": [{"id": device.id, "name": device.name or device.serial_number} for device in available_devices]}
    return JsonResponse(data)
    
def api_get_factory_devices(request, factory_id):
    """
    Fetch devices currently linked to the given factory.
    """
    factory = get_object_or_404(Factory, id=factory_id)
    devices = factory.devices.all()  # Assuming 'devices' is a related field in Factory model
    data = {"devices": [{"id": device.id, "name": device.name or device.serial_number} for device in devices]}
    return JsonResponse(data)
    
def pair_device(request):
    if request.method == 'POST':
        # Implement your logic for pairing devices here
        # For example, handle form submission and device pairing logic
        return HttpResponse("Device paired successfully")
    return redirect('manage_devices')  # Redirect to the main devices page or handle GET requests
    
def upload_factories(request):
    if request.method == 'POST':
        # Handle the uploaded file here
        return HttpResponse("Factories uploaded successfully!")
    return HttpResponse("Upload page")
    
def download_cities(request):
    # Logic to download cities
    # Example response for a file download:
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="cities.xlsx"'
    # Here you would add the logic to generate or serve the actual Excel file content
    return response
    
def upload_cities(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        # You can save the file using FileSystemStorage or process it immediately
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        # You can add code here to process the uploaded Excel file
        
        # After processing, you can redirect or render a success page
        return redirect('success_page')  # Redirect to a success page (create one or use an existing one)

    return redirect('super_admin')  # Redirect to your super admin page or another page in case of error
    
def download_devices(request):
    # Create the HttpResponse object with CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="devices.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header for the CSV file
    writer.writerow(['Device Name', 'Device Type', 'Serial Number'])

    # Fetch your device data from the database and write it to the CSV
    # Assuming you have a Device model (replace with actual model)
    devices = Device.objects.all()
    for device in devices:
        writer.writerow([device.name, device.type, device.serial_number])

    return response
    
def upload_devices(request):
    if request.method == 'POST':
        excel_file = request.FILES['excel_file']
        
        # Load the workbook and the sheet
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active
        
        # Assuming you have a Device model, loop through the sheet rows to save data
        for row in sheet.iter_rows(min_row=2, values_only=True):  # Skips header
            device_name, device_type, serial_number = row
            Device.objects.create(name=device_name, type=device_type, serial_number=serial_number)
        
        return redirect('super_admin')  # Redirect back to the admin page after upload
    else:
        return HttpResponse("Invalid request method", status=405)


  
def get_factory_status(request):
    factories = Factory.objects.all().values('id', 'status', 'error', 'devices')
    return JsonResponse({'factories': list(factories)})
    

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)


