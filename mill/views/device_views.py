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
            print("Update device counter called")
            selected_counter = request.POST.get('selected_counter')
            print(selected_counter)
            device.selected_counter = selected_counter
            device.save()
            messages.success(request, f"Counter updated for {device.id}: {selected_counter}")

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
