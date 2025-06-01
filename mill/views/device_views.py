from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from mill.models import Device , City
from mill.utils import admin_required, superadmin_required
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

@admin_required
def log_activity(user, obj, action_flag, change_message):
    """Helper function to log user activity"""
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=change_message
    )
# Function to get the highest counter value for the device for each day
@admin_required
def manage_devices(request):
    # Get all cities for the filter dropdown
    cities = City.objects.filter(status=True)
    
    # Get the selected city from the query parameters
    selected_city = request.GET.get('city')
    
    # Start with all devices query
    devices_query = Device.objects.all().select_related('factory__city')
    
    # Apply city filter if selected
    if selected_city:
        devices_query = devices_query.filter(factory__city_id=selected_city)
    
    # Convert queryset to list of dictionaries with city information
    devices_with_cities = []
    for device in devices_query:
        device_data = {
            'id': device.id,
            'name': device.name,
            'status': device.status,
            'selected_counter': device.selected_counter,
            'city': device.factory.city if device.factory and device.factory.city else None
        }
        devices_with_cities.append(device_data)

    if request.method == 'POST':
        action = request.POST.get('action')
        device_id = request.POST.get('device_id')
        device = get_object_or_404(Device, id=device_id)

        if action == 'update_device_counter':
            print("Update device counter called")
            selected_counter = request.POST.get('selected_counter')
            print(selected_counter)
            device.selected_counter = selected_counter
            device.save()
            messages.success(request, f"Counter updated for {device.id}: {selected_counter}")

        if action == 'rename_device':
            print("Rename device called")
            new_name = request.POST.get('new_device_name')
            device.name = new_name
            device.save()
            messages.success(request, f"Device renamed to {new_name}")

    return render(request, 'mill/manage_devices.html', {
        'existing_devices': devices_with_cities,
        'cities': cities,
        'selected_city': selected_city
    })


    existing_devices = Device.objects.all()
    return render(request, 'mill/manage_devices.html', {'existing_devices': existing_devices})
@admin_required
def add_device(request):
    if request.method == 'POST':
        device_name = request.POST.get('new_device_name')
        device_serial = request.POST.get('new_device_serial')

        # Ensure that both fields are provided
        if device_name and device_serial:
            Device.objects.create(name=device_name, id=device_serial)
            messages.success(request, 'Device added successfully.')
        else:
            messages.error(request, 'Please provide both device name and serial number.')

        return redirect('manage_devices')  # Redirect back to the manage devices page
@admin_required
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
@admin_required    
def remove_device(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        try:
            device = Device.objects.get(id=device_id)
            # device.delete()  # Remove the device from the database
        except Device.DoesNotExist:
            pass  # Handle the case where the device does not exist

    return redirect('manage_devices')  # Redirect back to the manage devices page
