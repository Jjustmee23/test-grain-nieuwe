from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from mill.utils import calculate_start_time, calculate_stop_time, check_factory_status
from mill.models import City, Factory, Device, ProductionData

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    # Grab all cities
    cities = City.objects.all()
    
    # Read city & date from query
    selected_city_id = request.GET.get('city')
    selected_date_str = request.GET.get('date')
    print(f"Received city={selected_city_id}, date={selected_date_str}")

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
    if not selected_city_id:
        selected_city_id = cities.first().id
    factories = Factory.objects.filter(city_id=selected_city_id)
    print(f"Factories found: {[f.id for f in factories]}")

    # One query for ProductionData across these factories
    production_qs = (
        ProductionData.objects
        .filter(device__factory__in=factories, created_at__date=selected_date)
        .values('device__factory')
        .annotate(
            daily_total=Sum('daily_production'),
            weekly_total=Sum('weekly_production'),
            monthly_total=Sum('monthly_production'),
            yearly_total=Sum('yearly_production'),
        )
    )
    # Convert into dict { factory_id: {...sums...} }
    sums_dict = {item['device__factory']: item for item in production_qs}
    print(f"Aggregated sums_dict: {sums_dict}")

    # Attach sums to each factory; also build city-wide totals in Python
    city_data = {
        'daily_total': 0, 'weekly_total': 0,
        'monthly_total': 0, 'yearly_total': 0
    }

    for factory in factories:
        sum_item = sums_dict.get(factory.id, {})
        factory.daily_total = sum_item.get('daily_total', 0) or 0
        factory.weekly_total = sum_item.get('weekly_total', 0) or 0
        factory.monthly_total = sum_item.get('monthly_total', 0) or 0
        factory.yearly_total = sum_item.get('yearly_total', 0) or 0

        # Accumulate city totals
        city_data['daily_total']   += factory.daily_total
        city_data['weekly_total']  += factory.weekly_total
        city_data['monthly_total'] += factory.monthly_total
        city_data['yearly_total']  += factory.yearly_total

        # Do status checks or other logic here as needed
        # factory.status = check_factory_status(...)

        print(f"Factory {factory.id} => D:{factory.daily_total} W:{factory.weekly_total} "
              f"M:{factory.monthly_total} Y:{factory.yearly_total}")

    print(f"Final city_data: {city_data}")

    context = {
        'cities': cities,
        'factories': factories,
        'selected_city_id': int(selected_city_id) if selected_city_id else None,
        'current_date': selected_date,
        'city_data': city_data
    }
    return render(request, 'mill/index.html', context)
