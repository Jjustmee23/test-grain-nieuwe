from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from mill.models import Device
from django.contrib import messages

# Function to get the highest counter value for the device for each day

def manage_devices(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        device_id = request.POST.get('device_id')
        device = get_object_or_404(Device, id=device_id)

        if action == 'update_device_counter':
            # Get the highest counter for the device
            highest_counters =None 
            # highest_counters =None or get_highest_counter(device.device_id)

            # Get the latest counter value for today
            if highest_counters and highest_counters[0] is not None:
                latest_counter_today = highest_counters[0]  # Highest value today
                if latest_counter_today != device.selected_counter:
                    device.selected_counter = latest_counter_today
                    device.save()
                    messages.success(request, f"Counter updated for {device.id}: {latest_counter_today}")
            else:
                messages.info(request, f"No new counters for {device.name} today.")
            return redirect('manage_devices')

    existing_devices = Device.objects.all()
    return render(request, 'mill/manage_devices.html', {'existing_devices': existing_devices})
 
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
            # device.delete()  # Remove the device from the database
        except Device.DoesNotExist:
            pass  # Handle the case where the device does not exist

    return redirect('manage_devices')  # Redirect back to the manage devices page
