from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from mill.utils import calculate_start_time, calculate_stop_time, check_factory_status
from mill.models import City
@login_required
def index(request):
    cities = City.objects.all()
    selected_city_id = request.GET.get('city')
    selected_date = timezone.now().date()

    context = {
        'cities': cities,
        'selected_city_id': selected_city_id,
        'current_date': selected_date,
    }
    return render(request, 'mill/index.html', context)
