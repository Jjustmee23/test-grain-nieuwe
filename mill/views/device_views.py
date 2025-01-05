from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from mill.models import Device

def get_devices(request):
    devices = Device.objects.all()
    devices_list = [{"id": device.id, "name": device.name or device.serial_number} for device in devices]
    return JsonResponse({"devices": devices_list})

def manage_devices(request):
    devices = Device.objects.all()
    return render(request, 'mill/manage_devices.html', {'devices': devices})
