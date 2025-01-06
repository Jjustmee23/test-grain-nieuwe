from django.http import JsonResponse
from mill.models import Device

def get_devices(request):
    devices = Device.objects.all()
    # Convert the devices QuerySet to a list of dictionaries
    devices_list = [{"id": device.id, "name": device.name or device.serial_number} for device in devices]
    return JsonResponse({"devices": devices_list})  # Use a string key for the JSON response
