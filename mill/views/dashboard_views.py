from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from mill.utils import calculate_start_time, calculate_stop_time, check_factory_status
from mill.models import City, Factory, Device, ProductionData
from django.db.models import Sum
from datetime import datetime
from mill.utils import allowed_cities

def index(request):
    return render(request, 'mill/index.html')



def _get_selected_city(request, cities):
    """Helper to get and validate selected city from request."""
    selected_city_id = request.GET.get('city')
    
    if selected_city_id == 'all':
        return 'all'
    
    if selected_city_id:
        try:
            selected_city_id = int(selected_city_id)
            if cities.filter(id=selected_city_id).exists():
                return selected_city_id
        except ValueError:
            pass
    
    return cities.first().id if cities.exists() else None

def _get_selected_date(request):
    """Helper to get and validate selected date from request."""
    selected_date_str = request.GET.get('date')
    
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            return min(selected_date, timezone.now().date())
        except ValueError:
            pass
    
    return timezone.now().date()

def _get_factories_for_city(selected_city_id):
    """Get factories for selected city or all factories if 'all' is selected."""
    if selected_city_id == 'all':
        return Factory.objects.all()
    return Factory.objects.filter(city_id=selected_city_id)

def _get_latest_production_data(factories, selected_date):
    """Get latest production data for devices in given factories."""
    devices = Device.objects.filter(factory__in=factories)
    production_qs = ProductionData.objects.filter(
        device__in=devices, 
        created_at__date=selected_date
    ).order_by('device_id', '-created_at')
    
    latest_production = {}
    for production in production_qs:
        if production.device_id not in latest_production:
            latest_production[production.device_id] = production
    return latest_production

def _calculate_totals(factories, latest_production):
    """Calculate factory and city totals from production data."""
    city_data = {
        'daily_total': 0, 
        'weekly_total': 0,
        'monthly_total': 0, 
        'yearly_total': 0
    }
    
    # First pass: calculate factory totals
    for factory in factories:
        factory_total = {
            'daily_total': 0, 
            'weekly_total': 0,
            'monthly_total': 0, 
            'yearly_total': 0
        }

        for production in latest_production.values():
            if production.device.factory_id == factory.id:
                factory_total['daily_total'] += production.daily_production or 0
                factory_total['weekly_total'] += production.weekly_production or 0
                factory_total['monthly_total'] += production.monthly_production or 0
                factory_total['yearly_total'] += production.yearly_production or 0

        # Attach totals to factory object
        factory.daily_total = factory_total['daily_total']
        factory.weekly_total = factory_total['weekly_total']
        factory.monthly_total = factory_total['monthly_total']
        factory.yearly_total = factory_total['yearly_total']
        
        # Accumulate city totals
        city_data['daily_total'] += factory.daily_total
        city_data['weekly_total'] += factory.weekly_total
        city_data['monthly_total'] += factory.monthly_total
        city_data['yearly_total'] += factory.yearly_total
    
    return city_data

@login_required
def dashboard(request):
    # Get user's allowed cities
    cities = allowed_cities(request)
    
    # Get and validate selected city and date
    selected_city_id = _get_selected_city(request, cities)
    selected_date = _get_selected_date(request)
    
    # If no cities are available, return empty context
    if not selected_city_id and selected_city_id != 'all':
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
            },
            'show_all_cities': False
        }
        return render(request, 'mill/dashboard.html', context)
    
    # Get factories based on selection
    factories = _get_factories_for_city(selected_city_id)
    latest_production = _get_latest_production_data(factories, selected_date)
    city_data = _calculate_totals(factories, latest_production)
    
    context = {
        'cities': cities,
        'factories': factories,
        'selected_city_id': selected_city_id if selected_city_id != 'all' else 'all',
        'current_date': selected_date,
        'city_data': city_data,
        'is_public': request.user.groups.filter(name='public').exists(),
        'show_all_cities': selected_city_id == 'all'
    }
    
    return render(request, 'mill/dashboard.html', context)