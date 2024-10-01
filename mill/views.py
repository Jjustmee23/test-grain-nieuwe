from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import user_passes_test, login_required
from .forms import CustomUserCreationForm, FactoryForm
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
import csv, openpyxl  
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import City, Factory, Device, DeviceData  
import logging
from datetime import datetime
from django.utils import timezone
from django.db.models import Sum  # Add this import


logger = logging.getLogger(__name__)


def manage_users(request):
    users = User.objects.all()  # Fetch all users
    print(users) 
    return render(request, 'mill/manage_users.html', {'users': users})

# Create new user view
@login_required
def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = UserCreationForm()
    return render(request, 'mill/create_user.html', {'form': form})

# Edit existing user view
@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = UserChangeForm(instance=user)
    return render(request, 'mill/edit_user.html', {'form': form, 'user': user})

# Delete user view
@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')
    return render(request, 'mill/delete_user.html', {'user': user})

# Assign permissions/rights to a user (e.g., add to group)
@login_required
def assign_rights(request, user_id):
    user = get_object_or_404(User, id=user_id)
    groups = Group.objects.all()  # Get all available groups (roles)
    
    if request.method == 'POST':
        selected_group = request.POST.get('group')
        group = Group.objects.get(name=selected_group)
        user.groups.add(group)
        return redirect('manage_users')

    return render(request, 'mill/assign_rights.html', {'user': user, 'groups': groups})

def index(request):
    # Haal alle steden op
    cities = City.objects.all()
    
    # Haal de geselecteerde stad op uit de GET-parameter 'city'
    selected_city_id = request.GET.get('city')
    
    # Haal de gekozen datum op uit de GET-parameter 'date'
    selected_date_str = request.GET.get('date')
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            # Als de gekozen datum in de toekomst ligt, zet terug naar vandaag
            if selected_date > timezone.now().date():
                selected_date = timezone.now().date()
        except ValueError:
            # Bij een ongeldige datum, zet de datum terug naar vandaag
            selected_date = timezone.now().date()
    else:
        # Als geen datum is geselecteerd, gebruik vandaag
        selected_date = timezone.now().date()

    # Filter de factories op basis van de geselecteerde stad
    if selected_city_id:
        factories = Factory.objects.filter(city_id=selected_city_id)
    else:
        # Als geen stad is geselecteerd, toon alle factories
        factories = Factory.objects.all()

    # Controleer de status van elke fabriek op basis van de laatste update (bijv. foutstatus)
    for factory in factories:
        factory.check_status()

        # Fetch daily total for the factory
        daily_total = DeviceData.objects.filter(
            device__factory=factory, 
            created_at__date=selected_date
        ).aggregate(
            daily_total=Sum('daily_total')  # Assuming counter_2 is the relevant counter for sacks
        )['daily_total'] or 0

        # Multiply to get tonnage (assuming 50 sacks = 1 ton)
        factory.daily_total = daily_total
        factory.daily_tons = daily_total * 50 / 1000

    context = {
        'cities': cities,
        'factories': factories,  # Voeg de gefilterde factories toe aan de context
        'selected_city_id': selected_city_id,
        'current_date': selected_date,  # Toon de gekozen of huidige datum
    }

    return render(request, 'mill/index.html', context)

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
    return render(request, 'mill/admin.html')

from django.utils.translation import get_language
from django.shortcuts import render

def super_admin_view(request):
    current_locale = get_language()  # Gets the current language
    dir = 'rtl' if current_locale == 'ar' else 'ltr'
    return render(request, 'mill/super_admin.html', {'dir': dir, 'lang': current_locale})

# Manage views for users, databases, devices, tables, factory, city, etc.
def manage_users(request):
    return render(request, 'mill/manage_users.html')

def manage_databases(request):
    return render(request, 'mill/manage_databases.html')

def manage_tables(request):
    return render(request, 'mill/manage_tables.html')

def manage_factory(request):
    if request.method == "POST":
        action = request.POST.get("action")
        factory_id = request.POST.get("factory_id")
        
        if action == "remove_factory":
            factory = Factory.objects.get(id=factory_id)
            factory.delete()  # Delete the factory
            messages.success(request, _("Factory removed successfully."))
            return redirect("manage_factory")

def manage_city(request):
    return render(request, 'mill/manage_city.html')

from datetime import date

def view_statistics(request):
    selected_date = request.GET.get('date', date.today().isoformat())
    context = {
        'date': selected_date,
        'current_date': date.today().isoformat(),
    }
    
    return render(request, 'mill/view_statistics.html', context)

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
        
def manage_city(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        city_name = request.POST.get('city_name')

        logger.info(f"Action: {action}, City Name: {city_name}")

        if action == 'add_city':
            # Validate city name
            if not city_name.strip():
                messages.error(request, 'City name cannot be empty!')
                return redirect('manage_city')
            
            try:
                # Add new city
                City.objects.create(name=city_name)
                messages.success(request, 'City added successfully!')
            except Exception as e:
                logger.error(f"Error saving city: {e}")
                messages.error(request, 'Error adding city!')
            
        return redirect('manage_city')

    # GET request: show the list of cities
    cities = City.objects.all()
    return render(request, 'mill/manage_city.html', {'cities': cities})
    
def manage_factory(request):
    if request.method == "POST":
        action = request.POST.get('action')
        factory_id = request.POST.get('factory_id')
        device_id = request.POST.get('device_id')

        if action == "add_device_to_factory":
            # Linking device to factory
            factory = get_object_or_404(Factory, id=factory_id)
            device = get_object_or_404(Device, id=device_id)
            if device.factory is None:  # Check if device is not already linked
                device.factory = factory
                device.save()
                messages.success(request, f"Device '{device.name}' linked to factory '{factory.name}'.")
            else:
                messages.error(request, "Device is already linked to another factory.")
        
        elif action == "remove_device_from_factory":
            # Unlinking device from factory
            factory = get_object_or_404(Factory, id=factory_id)
            device = get_object_or_404(Device, id=device_id)
            if device.factory == factory:
                device.factory = None  # Unlink the device
                device.save()
                messages.success(request, f"Device '{device.name}' unlinked from factory '{factory.name}'.")
            else:
                messages.error(request, "Device is not linked to this factory.")
        
        elif action == "remove_factory":
            factory = Factory.objects.get(id=factory_id)
            factory.delete()
            messages.success(request, _("Factory removed successfully."))

        elif action == "add_factory":
            factory_name = request.POST.get('factory_name')
            city_id = request.POST.get('city_id')
            factory = Factory(name=factory_name)
            if city_id:
                city = City.objects.get(id=city_id)
                factory.city = city
            factory.save()
            messages.success(request, f"Factory '{factory_name}' has been added.")
        
        return redirect("manage_factory")

    cities = City.objects.all()
    factories = Factory.objects.all().select_related('city')
    return render(request, 'mill/manage_factory.html', {'factories': factories, 'cities': cities})
    
    
# Function to get the highest counter value for the device for each day
def get_highest_counter(device_id):
    # Query the external MQTT database for the device's counter values in the last day
    cursor = connections['mqtt_db'].cursor()
    cursor.execute("""
        SELECT MAX(counter), DATE(created_at)
        FROM mqtt_data
        WHERE device_id = %s
        GROUP BY DATE(created_at)
        ORDER BY created_at DESC
    """, [device_id])
    
    return cursor.fetchall()

def manage_devices(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        device_id = request.POST.get('device_id')
        device = get_object_or_404(Device, id=device_id)

        if action == 'update_device_counter':
            # Get the highest counter for the device
            highest_counters = get_highest_counter(device.device_id)

            # Get the latest counter value for today
            if highest_counters and highest_counters[0] is not None:
                latest_counter_today = highest_counters[0]  # Highest value today
                if latest_counter_today != device.selected_counter:
                    device.selected_counter = latest_counter_today
                    device.save()
                    messages.success(request, f"Counter updated for {device.device_id}: {latest_counter_today}")
            else:
                messages.info(request, f"No new counters for {device.device_id} today.")
            return redirect('manage_devices')

    existing_devices = Device.objects.all()
    return render(request, 'mill/manage_devices.html', {'existing_devices': existing_devices})
    
def get_factory_status(request):
    factories = Factory.objects.all().values('id', 'status', 'error', 'devices')
    return JsonResponse({'factories': list(factories)})
    
def add_device(request):
    if request.method == 'POST':
        device_name = request.POST.get('new_device_name')
        device_serial = request.POST.get('new_device_serial')

        # Ensure that both fields are provided
        if device_name and device_serial:
            Device.objects.create(name=device_name, serial_number=device_serial)
            messages.success(request, 'Device added successfully.')
        else:
            messages.error(request, 'Please provide both device name and serial number.')

        return redirect('manage_devices')  # Redirect back to the manage devices page

def toggle_device_status(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        try:
            device = Device.objects.get(id=device_id)
            device.status = not device.status  # Toggle the status
            device.save()
        except Device.DoesNotExist:
            pass  # Handle the case where the device does not exist

    return redirect('manage_devices')  # Redirect back to the manage devices page
    
def remove_device(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        try:
            device = Device.objects.get(id=device_id)
            device.delete()  # Remove the device from the database
        except Device.DoesNotExist:
            pass  # Handle the case where the device does not exist

    return redirect('manage_devices')  # Redirect back to the manage devices page