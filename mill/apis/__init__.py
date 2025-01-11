from django.http import JsonResponse
from mill.models import Device
from mill.utils import calculate_chart_data

def get_devices(request):
    devices = Device.objects.all()
    # Convert the devices QuerySet to a list of dictionaries
    devices_list = [{"id": device.id, "name": device.name or device.serial_number} for device in devices]
    return JsonResponse({"devices": devices_list})  # Use a string key for the JSON response

def chart_data(request):
    factory_id = request.GET.get('factory_id')
    date = request.GET.get('date')
    print(date), print(factory_id)
    if not factory_id or not date:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    chart_data = calculate_chart_data(date, factory_id)
    print(chart_data)
    return JsonResponse(chart_data)