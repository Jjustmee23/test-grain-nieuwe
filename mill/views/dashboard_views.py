from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from mill.utils import calculate_start_time, calculate_stop_time, check_factory_status
from mill.models import City, Factory, Device, ProductionData
from django.db.models import Sum
from datetime import datetime

@login_required
def index(request):
    # Grab all cities
    if request.user.groups.filter(name='super_admin').exists():
        cities = City.objects.all()
    else:
        cities = request.user.userprofile.allowed_cities.all()    
    
    # Read city & date from query
    selected_city_id = request.GET.get('city')
    selected_date_str = request.GET.get('date')

    # Validate selected city is in user's allowed cities
    if selected_city_id:
        try:
            selected_city_id = int(selected_city_id)
            if not cities.filter(id=selected_city_id).exists():
                selected_city_id = cities.first().id if cities.exists() else None
        except ValueError:
            selected_city_id = cities.first().id if cities.exists() else None
    else:
        selected_city_id = cities.first().id if cities.exists() else None

    # If no cities are available, return empty context
    if not selected_city_id:
        context = {
            'cities': cities,
            'factories': Factory.objects.none(),
            'selected_city_id': None,
            'current_date': timezone.now().date(),
            'city_data': {
                'daily_total': 0,
                'weekly_total': 0,
                'monthly_total': 0,
                'yearly_total': 0
            }
        }
        return render(request, 'mill/index.html', context)

    # Validate/parse date; default to today if invalid
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            if selected_date > timezone.now().date():
                selected_date = timezone.now().date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    print(f"Final selected_date={selected_date}")

    # Filter factories
    factories = Factory.objects.filter(city_id=selected_city_id)
    print(f"Factories found: {[f.id for f in factories]}")

    # Query Devices
    devices = Device.objects.filter(factory__in=factories)
    # One query for ProductionData across these factories
    production_qs = ProductionData.objects.filter(
    device__in=devices, created_at__date=selected_date).order_by('device_id', '-created_at')
    # Dictionary to store the latest production data per device
    latest_production = {}
    for production in production_qs:
        if production.device_id not in latest_production:
            latest_production[production.device_id] = production
    # Attach sums to each factory; also build city-wide totals in Python
    # Initialize city-wide totals
    city_data = {
        'daily_total': 0, 'weekly_total': 0,
        'monthly_total': 0, 'yearly_total': 0
    }
    print(f"latest_production: {latest_production}")
    # Iterate through factories and attach the latest data
    for factory in factories:
        # Find the latest production data for any device in this factory
        factory_total = {
            'daily_total': 0, 'weekly_total': 0,
            'monthly_total': 0, 'yearly_total': 0
        }

        for production in latest_production.values():
            print(f"production.device.factory_id | daily_total: {production.device.factory_id} {factory_total['weekly_total']}")
            if production.device.factory_id == factory.id:
                factory_total['daily_total'] += production.daily_production or 0
                factory_total['weekly_total'] += production.weekly_production or 0
                factory_total['monthly_total'] += production.monthly_production or 0
                factory_total['yearly_total'] += production.yearly_production or 0

        # Attach totals to the factory
        factory.daily_total = factory_total['daily_total']
        factory.weekly_total = factory_total['weekly_total']
        factory.monthly_total = factory_total['monthly_total']
        factory.yearly_total = factory_total['yearly_total']

        # Accumulate into city totals
        city_data['daily_total'] += factory.daily_total
        city_data['weekly_total'] += factory.weekly_total
        city_data['monthly_total'] += factory.monthly_total
        city_data['yearly_total'] += factory.yearly_total

        # Debugging output (optional)
        print(f"Factory {factory.id} => "
            f"D:{factory.daily_total} W:{factory.weekly_total} "
            f"M:{factory.monthly_total} Y:{factory.yearly_total}")

    # Debugging output for final city totals
    print(f"Final city_data: {city_data}")
    context = {
        'cities': cities,
        'factories': factories,
        'selected_city_id': int(selected_city_id) if selected_city_id else None,
        'current_date': selected_date,
        'city_data': city_data,
        'is_public': request.user.groups.filter(name='public').exists()
    }
    return render(request, 'mill/index.html', context)
