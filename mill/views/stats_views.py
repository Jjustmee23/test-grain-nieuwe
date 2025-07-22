from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device, UserProfile, Batch, FlourBagCount
from django.contrib import messages
from datetime import date, datetime
from django.db.models import Sum
from django.db.models.functions import TruncHour
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from mill.utils.chart_handler_utils import calculate_chart_data, calculate_device_chart_data
from mill.utils.permmissions_handler_utils import is_allowed_factory
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import json

@login_required
def view_statistics(request, factory_id):
    # Get the factory first
    factory = get_object_or_404(Factory, id=factory_id)
    
    # Check user permissions
    if not request.user.is_superuser:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            if not user_profile.allowed_factories.filter(id=factory_id).exists():
                messages.error(request, "You don't have permission to access this factory.")
                return redirect('index')
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
            return redirect('index')

    # Get devices for this factory
    devices = Device.objects.filter(factory=factory).order_by('name')
    
    # Get selected device from query parameters
    selected_device_id = request.GET.get('device_id', 'all')

    # Get batches for this specific factory only
    batches = Batch.objects.filter(
        factory=factory  # This ensures we only get batches for the current factory
    ).select_related('factory').prefetch_related(
        'flour_bag_counts',
        'alerts'
    ).order_by('-created_at')

    batch_details = []
    for batch in batches:
        # Calculate yield rate
        yield_rate = float(batch.actual_flour_output) / float(batch.expected_flour_output) * 100 if batch.expected_flour_output else 0
        
        batch_detail = {
            'id': batch.id,
            'batch_number': batch.batch_number,
            'start_date': batch.start_date.isoformat() if batch.start_date else None,  # Convert to ISO format for JSON
            'status': batch.get_status_display(),
            'is_completed': batch.is_completed,
            'wheat_amount': float(batch.wheat_amount or 0),
            'expected_flour_output': float(batch.expected_flour_output or 0),
            'actual_flour_output': float(batch.actual_flour_output or 0),
            'waste_factor': float(batch.waste_factor or 0),
            'yield_rate': yield_rate,
            'detail_url': reverse('batch-detail', kwargs={'pk': batch.id})
        }
        batch_details.append(batch_detail)

    # Convert batch_details to JSON-safe format
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    batch_details_json = json.dumps(batch_details, cls=DjangoJSONEncoder)

    context = {
        'factory': factory,
        'devices': devices,
        'selected_device_id': selected_device_id,
        'selected_date': timezone.now().date(),
        'current_year': datetime.now().year,
        'batches': batch_details_json,
        'total_batches': len(batch_details),
        'factory_id': factory_id  # Add factory_id to context
    }

    return render(request, 'mill/view_statistics.html', context)

@login_required
def get_device_chart_data(request, factory_id):
    """API endpoint to get chart data filtered by device"""
    try:
        # Get the factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Check user permissions
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    return JsonResponse({'error': 'Permission denied'}, status=403)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'User profile not found'}, status=403)
        
        # Get parameters
        selected_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
        device_id = request.GET.get('device_id', 'all')
        
        # Parse date
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
        
        # Get chart data based on device filter
        if device_id == 'all':
            # Use existing function for all devices
            chart_data = calculate_chart_data(selected_date, factory_id)
        else:
            # Filter by specific device
            chart_data = calculate_device_chart_data(selected_date, factory_id, device_id)
        
        return JsonResponse(chart_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)