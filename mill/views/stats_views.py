from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device
from datetime import date, datetime
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from mill.utils import calculate_chart_data, is_allowed_factory


@login_required
def view_statistics(request, factory_id):
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


    # Summarize production data for this factory on the selected date
    production_qs = (
        ProductionData.objects
        .filter(device__factory=factory, created_at__date=selected_date)
        .values('device__factory')
        .annotate(
            daily_total=Sum('daily_production'),
            weekly_total=Sum('weekly_production'),
            monthly_total=Sum('monthly_production'),
            yearly_total=Sum('yearly_production'),
        )
    )
    print(f"Production data for {factory.name} on {selected_date}: {production_qs}")
    # Convert results to a dict for easy lookup
    sums_dict = production_qs[0] if production_qs.exists() else {}

    # Attach sums to factory (use .get() with default 0 if not found)
    factory.daily_total = sums_dict.get('daily_total', 0) or 0
    factory.weekly_total = sums_dict.get('weekly_total', 0) or 0
    factory.monthly_total = sums_dict.get('monthly_total', 0) or 0
    factory.yearly_total = sums_dict.get('yearly_total', 0) or 0

    # chart_data = calculate_chart_data(selected_date, factory_id)
    context = {
        'factory': factory,
        'selected_date': selected_date,
        # 'chart_data': chart_data,
    }    
    # Render the HTML template with the context
    return render(request, 'mill/view_statistics.html', context)
