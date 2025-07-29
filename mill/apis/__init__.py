from django.http import JsonResponse
from mill.models import Device, City, Factory
from mill.utils.chart_handler_utils import calculate_chart_data, calculate_batch_chart_data, calculate_date_range_data

def get_devices(request):
    devices = Device.objects.all()
    # Convert the devices QuerySet to a list of dictionaries
    devices_list = [{"id": device.id, "name": device.name or device.serial_number} for device in devices]
    return JsonResponse({"devices": devices_list})  # Use a string key for the JSON response

def get_city_factories(request, city_id):
    """Get all factories for a specific city"""
    try:
        city = City.objects.get(id=city_id, status=True)
        factories = Factory.objects.filter(city=city, status=True).order_by('name')
        
        factories_list = [
            {"id": factory.id, "name": factory.name, "city_name": city.name, "city_id": city.id} 
            for factory in factories
        ]
        
        return JsonResponse({
            "city": {"id": city.id, "name": city.name},
            "factories": factories_list
        })
    except City.DoesNotExist:
        return JsonResponse({'error': 'City not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_all_factories(request):
    """Get all factories"""
    try:
        factories = Factory.objects.filter(status=True).order_by('name')
        
        factories_list = [
            {"id": factory.id, "name": factory.name, "city_name": factory.city.name if factory.city else "Unknown", "city_id": factory.city.id if factory.city else None} 
            for factory in factories
        ]
        
        return JsonResponse({
            "factories": factories_list
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def chart_data(request):
    factory_id = request.GET.get('factory_id')
    date = request.GET.get('date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    print(f"Factory ID: {factory_id}, Date: {date}, Start: {start_date}, End: {end_date}")
    
    if not factory_id:
        return JsonResponse({'error': 'Factory ID is required'}, status=400)
    
    try:
        if start_date and end_date:
            # Date range calculation
            print(f"Calculating date range data for {start_date} to {end_date}")
            chart_data = calculate_date_range_data(factory_id, start_date, end_date)
        elif date:
            # Single date calculation
            print(f"Calculating single date data for {date}")
            chart_data = calculate_chart_data(date, factory_id)
        else:
            # Default to today
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"Using default date: {today}")
            chart_data = calculate_chart_data(today, factory_id)
        
        print(chart_data)
        return JsonResponse(chart_data)
        
    except Exception as e:
        print(f"Error in chart_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def batch_chart_data(request):
    print("batch_chart_data")
    batch_id = request.GET.get('batch_id')
    if not batch_id :
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    chart_data = calculate_batch_chart_data(batch_id)
    return JsonResponse(chart_data)

