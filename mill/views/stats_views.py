from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device, UserProfile, Batch, FlourBagCount, DevicePowerStatus, PowerEvent, PowerManagementPermission
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

    # Power management data (only for super admins)
    power_management_data = None
    if request.user.is_superuser:
        # Get power status for devices in this factory
        power_statuses = DevicePowerStatus.objects.filter(device__factory=factory)
        
        # Get power events for this factory (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        power_events = PowerEvent.objects.filter(
            device__factory=factory,
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:10]
        
        # Calculate power statistics
        devices_with_power = power_statuses.filter(has_power=True).count()
        devices_without_power = power_statuses.filter(has_power=False).count()
        total_devices_power = power_statuses.count()
        uptime_percentage = (devices_with_power / total_devices_power * 100) if total_devices_power > 0 else 100
        
        # Power consumption trends (simulated data)
        avg_power_consumption = 12.5  # kW
        peak_power_usage = 15.2  # kW
        power_efficiency_score = 85.5  # /100
        energy_cost_savings = 1250.75  # €
        
        power_management_data = {
            'power_statuses': list(power_statuses.values('device__name', 'has_power', 'ain1_value', 'last_power_check')),
            'recent_power_events': list(power_events.values('event_type', 'severity', 'created_at', 'device__name', 'message')),
            'devices_with_power': devices_with_power,
            'devices_without_power': devices_without_power,
            'total_devices_power': total_devices_power,
            'uptime_percentage': uptime_percentage,
            'avg_power_consumption': avg_power_consumption,
            'peak_power_usage': peak_power_usage,
            'power_efficiency_score': power_efficiency_score,
            'energy_cost_savings': energy_cost_savings,
        }

    context = {
        'factory': factory,
        'devices': devices,
        'selected_device_id': selected_device_id,
        'selected_date': timezone.now().date(),
        'current_year': datetime.now().year,
        'batches': batch_details_json,
        'total_batches': len(batch_details),
        'factory_id': factory_id,  # Add factory_id to context
        'power_management_data': power_management_data,  # Power management data for super admins
        'is_superuser': request.user.is_superuser,  # Flag to show/hide power management sections
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