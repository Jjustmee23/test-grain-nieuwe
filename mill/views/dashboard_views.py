from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from mill.utils import calculate_start_time, calculate_stop_time, check_factory_status, allowed_cities, allowed_factories
from mill.models import City, Factory, Device, ProductionData, DoorOpenLogs
from django.db.models import Sum
from datetime import datetime
from mill.utils import allowed_cities

def index(request):
    return render(request, 'mill/index.html')

@login_required
def dashboard(request):
    # Get current user's timezone-aware datetime
    current_datetime = timezone.now()
    
    # Grab all cities
    cities= allowed_cities(request)
    
    # Read cities & date from query
    selected_cities_param = request.GET.get('cities')
    selected_date_str = request.GET.get('date', current_datetime.strftime('%Y-%m-%d'))

    # Handle multiple city selection
    selected_city_ids = []
    if selected_cities_param:
        try:
            selected_city_ids = [int(city_id) for city_id in selected_cities_param.split(',')]
            # Validate selected cities are in user's allowed cities
            selected_city_ids = [
                city_id for city_id in selected_city_ids 
                if cities.filter(id=city_id).exists()
            ]
        except ValueError:
            selected_city_ids = []

    # If no cities are selected or invalid selection, use all available cities
    # Check if explicitly unselecting all cities
    unselect_all = request.GET.get('unselect_all', 'false') == 'true'

    # If no cities are selected or invalid selection, and not explicitly unselecting all
    if not selected_city_ids and not unselect_all:
        selected_city_ids = list(cities.values_list('id', flat=True))
    elif not selected_city_ids and unselect_all:
        selected_city_ids = []

    # Validate/parse date
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        if selected_date > current_datetime.date():
            selected_date = current_datetime.date()
    except ValueError:
        selected_date = current_datetime.date()

    # Filter factories for selected cities
    factories =  allowed_factories(request).filter(city_id__in=selected_city_ids)

    # Query Devices with select_related to reduce queries
    devices = Device.objects.filter(factory__in=factories).select_related('factory')
    
    # Optimize production data query
    production_qs = ProductionData.objects.filter(
        device__in=devices, 
        created_at__date=selected_date
    ).select_related('device').order_by('device_id', '-created_at')

    # Process production data
    latest_production = {}
    for production in production_qs:
        if production.device_id not in latest_production:
            latest_production[production.device_id] = production

    # Initialize city-wide totals
    city_data = {
        'daily_total': 0,
        'weekly_total': 0,
        'monthly_total': 0,
        'yearly_total': 0
    }

    # Process factory data
    for factory in factories:
        factory_total = {
            'daily_total': 0,
            'weekly_total': 0,
            'monthly_total': 0,
            'yearly_total': 0
        }

        factory_devices = [d for d in devices if d.factory_id == factory.id]
        for device in factory_devices:
            if device.id in latest_production:
                production = latest_production[device.id]
                factory_total['daily_total'] += production.daily_production or 0
                factory_total['weekly_total'] += production.weekly_production or 0
                factory_total['monthly_total'] += production.monthly_production or 0
                factory_total['yearly_total'] += production.yearly_production or 0

        # Attach totals to the factory
        for key, value in factory_total.items():
            setattr(factory, key, value)
            city_data[key] += value

    for factory in factories:
        # Get the latest unresolved door log for any device in this factory
        latest_door_log = DoorOpenLogs.objects.filter(
            device__factory=factory,
            is_resolved=False
        ).first()
        
        factory.status_info = {
            'power_status': factory.status,  # Use existing status for power
            'door_status': latest_door_log is not None  # True if there's an unresolved door log
        }

    context = {
        'cities': cities,
        'factories': factories,
        'selected_city_ids': selected_city_ids,
        'current_date': selected_date,
        'city_data': city_data,
        'is_public': request.user.groups.filter(name='public').exists(),
        'current_user': request.user.username,
        'current_datetime': current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    }
    return render(request, 'mill/dashboard.html', context)

@login_required
def resolve_door_alert(request, log_id):
    if request.method == 'POST':
        try:
            door_log = DoorOpenLogs.objects.get(id=log_id, is_resolved=False)
            door_log.is_resolved = True
            door_log.resolved_by = request.user
            door_log.resolved_at = timezone.now()
            door_log.save()
            return JsonResponse({'status': 'success'})
        except DoorOpenLogs.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Log not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)