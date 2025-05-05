from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, F
from django.db.models.functions import TruncDate, TruncHour
from mill.models import Batch, FlourBagCount
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.http import JsonResponse


@login_required
def analytics_dashboard(request):
    # Get date range from request or default to last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = request.GET.get('date_range', '30')  # default to 30 days

    # Get factory filter
    factory_id = request.GET.get('factory')

    # Base queryset
    batches = Batch.objects.filter(
        created_at__range=[start_date, end_date]
    )
    
    if factory_id:
        batches = batches.filter(factory_id=factory_id)

    # Calculate KPIs
    kpis = {
        'total_batches': batches.count(),
        'total_wheat': batches.aggregate(Sum('wheat_amount'))['wheat_amount__sum'] or 0,
        'total_flour': batches.aggregate(Sum('actual_flour_output'))['actual_flour_output__sum'] or 0,
        'average_yield': batches.annotate(
            yield_ratio=(F('actual_flour_output') / F('wheat_amount') * 100)
        ).aggregate(Avg('yield_ratio'))['yield_ratio__avg'] or 0,
    }

    # Daily production data
    daily_production = batches.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        wheat_amount=Sum('wheat_amount'),
        flour_output=Sum('actual_flour_output')
    ).order_by('date')

    return render(request, 'analytics/dashboard.html', {
        'kpis': kpis,
        'daily_production': daily_production,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def batch_performance(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    
    # Get hourly production data
    hourly_data = batch.flour_bag_counts.annotate(
        hour=TruncHour('timestamp')
    ).values('hour').annotate(
        total_bags=Sum('bag_count'),
        total_weight=Sum('bags_weight')
    ).order_by('hour')

    return render(request, 'analytics/batch_details.html', {
        'batch': batch,
        'hourly_data': hourly_data,
    })

def batch_update(request, pk):
    if request.method == 'POST':
        batch = get_object_or_404(Batch, pk=pk)
        try:
            # Update batch with form data
            batch.wheat_amount = float(request.POST.get('wheat_amount', batch.wheat_amount))
            batch.waste_factor = float(request.POST.get('waste_factor', batch.waste_factor))
            batch.actual_flour_output = float(request.POST.get('actual_flour_output', batch.actual_flour_output))
            batch.is_completed = request.POST.get('is_completed') == 'true'
            batch.save()

            # Return success response with updated data
            return JsonResponse({
                'success': True,
                'message': 'Batch updated successfully',
                'batch_data': {
                    'wheat_amount': batch.wheat_amount,
                    'expected_flour_output': batch.expected_flour_output,
                    'actual_flour_output': batch.actual_flour_output,
                    'waste_factor': batch.waste_factor,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def batch_detail(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    yield_rate = (batch.actual_flour_output / batch.expected_flour_output * 100) if batch.expected_flour_output else 0
    
    context = {
        'batch': batch,
        'yield_rate': yield_rate,
        'alerts': batch.alerts.all() if hasattr(batch, 'alerts') else [],
    }
    return render(request, 'mill/batch_details.html', context)