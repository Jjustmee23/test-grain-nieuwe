from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device
from datetime import date, datetime
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from mill.utils import calculate_chart_data, is_allowed_factory


@login_required
def view_statistics(request, factory_id):
    context = {
        'current_year': datetime.now().year,
    }
    # Read factory & date from query
    selected_date_str = request.GET.get('date')
    
    # Get the actual factory object
    factory = is_allowed_factory(request, factory_id)
    if not factory:
        return redirect('index')
    # Validate/parse date or use today
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            if selected_date > timezone.now().date():
                selected_date = timezone.now().date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()


    # Summarize production data for this factory on the selected d    
    production_qs = ProductionData.objects.filter(
    device__factory=factory, created_at__date=selected_date).order_by('device_id', '-created_at')
    # Dictionary to store the latest production data per device
    latest_production = {}
    for production in production_qs:
        if production.device_id not in latest_production:
            latest_production[production.device_id] = production

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

    # Attach sums to factory (use .get() with default 0 if not found)
    # Attach totals to the factory
    factory.daily_total = factory_total['daily_total']
    factory.weekly_total = factory_total['weekly_total']
    factory.monthly_total = factory_total['monthly_total']
    factory.yearly_total = factory_total['yearly_total']

    # chart_data = calculate_chart_data(selected_date, factory_id)
    context = {
        'factory': factory,
        'selected_date': selected_date,
        'yearly_previous': 0,
        # 'chart_data': chart_data,
    }    
      # Render the HTML template with the context
    return render(request, 'mill/view_statistics.html', context)
