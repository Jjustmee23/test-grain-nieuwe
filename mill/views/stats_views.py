from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device, UserProfile, Batch, FlourBagCount, DevicePowerStatus, PowerEvent, PowerManagementPermission, DoorStatus, DoorOpenLogs, RawData, PowerData
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
    device_count = devices.count()
    
    # Get selected device from query parameters
    selected_device_id = request.GET.get('device_id', 'all')
    
    # Auto-select device logic: if only one device, select it; if multiple devices, default to 'all'
    if device_count == 1:
        # If only one device, always select it
        selected_device_id = str(devices.first().id)
    elif not selected_device_id or selected_device_id == 'all':
        # If multiple devices and no specific device selected, default to 'all'
        selected_device_id = 'all'

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

    # Door status data
    door_statuses = DoorStatus.objects.filter(device__factory=factory).select_related('device')
    door_status_data = []
    for door_status in door_statuses:
        door_status_data.append({
            'device_name': door_status.device.name,
            'device_id': door_status.device.id,
            'is_open': door_status.is_open,
            'status_display': door_status.get_status_display(),
            'status_color': door_status.get_status_color(),
            'last_check': door_status.last_check.isoformat() if door_status.last_check else None,
            'last_din_data': door_status.last_din_data,
            'door_input_index': door_status.door_input_index
        })



    context = {
        'factory': factory,
        'devices': devices,
        'device_count': device_count,
        'selected_device_id': selected_device_id,
        'selected_date': timezone.now().date(),
        'current_year': datetime.now().year,
        'batches': batch_details_json,
        'total_batches': len(batch_details),
        'factory_id': factory_id,  # Add factory_id to context
        'door_status_data': door_status_data,  # Door status data
    }

    return render(request, 'mill/view_statistics.html', context)

@login_required
def get_door_status_data(request, factory_id):
    """API endpoint to get door status data for a factory"""
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
        
        # Get device filter from request
        device_id = request.GET.get('device_id', 'all')
        
        # Get door statuses for this factory (most recent data)
        if device_id == 'all':
            door_statuses = DoorStatus.objects.filter(device__factory=factory).select_related('device').order_by('-updated_at')
        else:
            door_statuses = DoorStatus.objects.filter(device__factory=factory, device_id=device_id).select_related('device').order_by('-updated_at')
        
        # Get recent door logs (last 24 hours for real-time monitoring)
        one_day_ago = timezone.now() - timezone.timedelta(hours=24)
        if device_id == 'all':
            recent_door_logs = DoorOpenLogs.objects.filter(
                device__factory=factory,
                timestamp__gte=one_day_ago
            ).select_related('device').order_by('-timestamp')[:50]
        else:
            recent_door_logs = DoorOpenLogs.objects.filter(
                device__factory=factory,
                device_id=device_id,
                timestamp__gte=one_day_ago
            ).select_related('device').order_by('-timestamp')[:50]
        
        door_status_data = []
        for door_status in door_statuses:
            # Get the most recent RawData for this device to ensure real-time status
            latest_raw_data = RawData.objects.filter(device=door_status.device).order_by('-timestamp').first()
            
            # Update door status based on latest RawData if available
            if latest_raw_data and latest_raw_data.din:
                din_values = [int(x) for x in latest_raw_data.din.split('.') if x.isdigit()]
                if len(din_values) > door_status.door_input_index:
                    is_open = bool(din_values[door_status.door_input_index])
                    # Update the door status if it changed
                    if door_status.is_open != is_open:
                        door_status.is_open = is_open
                        door_status.last_din_data = latest_raw_data.din
                        door_status.last_check = latest_raw_data.timestamp
                        door_status.save()
            
            door_status_data.append({
                'device_name': door_status.device.name,
                'device_id': door_status.device.id,
                'is_open': door_status.is_open,
                'status_display': door_status.get_status_display(),
                'status_color': door_status.get_status_color(),
                'last_check': door_status.last_check.isoformat() if door_status.last_check else None,
                'last_din_data': door_status.last_din_data,
                'door_input_index': door_status.door_input_index,
                'last_raw_data_timestamp': latest_raw_data.timestamp.isoformat() if latest_raw_data else None
            })
        
        door_logs_data = []
        for log in recent_door_logs:
            door_logs_data.append({
                'id': log.id,
                'device_name': log.device.name,
                'device_id': log.device.id,
                'timestamp': log.timestamp.isoformat(),
                'din_data': log.din_data,
                'door_input_index': log.door_input_index,
                'is_resolved': log.is_resolved,
                'resolved_by': log.resolved_by.username if log.resolved_by else None,
                'resolved_at': log.resolved_at.isoformat() if log.resolved_at else None
            })
        
        return JsonResponse({
            'door_statuses': door_status_data,
            'recent_logs': door_logs_data,
            'total_doors': len(door_status_data),
            'open_doors': len([d for d in door_status_data if d['is_open']]),
            'closed_doors': len([d for d in door_status_data if not d['is_open']])
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

@login_required
def get_power_status_data(request, factory_id):
    """Get power status data for a factory"""
    try:
        # Check permissions
        if not request.user.is_superuser and not PowerManagementPermission.has_power_status_access(request.user):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Get device filter from request
        device_id = request.GET.get('device_id', 'all')
        
        # Get devices for this factory
        if device_id == 'all':
            devices = Device.objects.filter(factory=factory)
        else:
            devices = Device.objects.filter(factory=factory, id=device_id)
        
        # Get power status for each device (most recent data)
        power_statuses = DevicePowerStatus.objects.filter(device__in=devices).select_related('device').order_by('-last_check')
        
        # Prepare device data
        devices_data = []
        devices_without_power = 0
        
        for device in devices:
            power_status = power_statuses.filter(device=device).first()
            
            # Get the most recent RawData for this device to ensure real-time power status
            latest_raw_data = RawData.objects.filter(device=device).order_by('-timestamp').first()
            
            # Update power status based on latest RawData if available
            if latest_raw_data and latest_raw_data.ain1 is not None:
                try:
                    ain1_value = float(latest_raw_data.ain1)
                    has_power = ain1_value > 0  # Threshold for power detection (any positive value)
                    
                    # Always update AIN1 value to ensure accuracy
                    if power_status:
                        power_status.ain1_value = ain1_value
                        power_status.last_check = latest_raw_data.timestamp
                        
                        # Update power status if it changed
                        if power_status.has_power != has_power:
                            power_status.has_power = has_power
                            if not has_power:
                                power_status.power_loss_detected_at = latest_raw_data.timestamp
                            else:
                                power_status.power_restored_at = latest_raw_data.timestamp
                        
                        power_status.save()
                    else:
                        # Create new power status if it doesn't exist
                        power_status = DevicePowerStatus.objects.create(
                            device=device,
                            has_power=has_power,
                            ain1_value=ain1_value,
                            last_check=latest_raw_data.timestamp,
                            power_loss_detected_at=latest_raw_data.timestamp if not has_power else None
                        )
                except (ValueError, TypeError) as e:
                    print(f"Error parsing AIN1 value for device {device.name}: {e}")
                    # Keep existing power status if AIN1 parsing fails
            
            # Get the most accurate AIN1 value from latest RawData
            accurate_ain1_value = None
            if latest_raw_data and latest_raw_data.ain1 is not None:
                try:
                    raw_ain1 = latest_raw_data.ain1
                    # Handle different data types and formats
                    if isinstance(raw_ain1, (int, float)):
                        accurate_ain1_value = float(raw_ain1)
                    elif isinstance(raw_ain1, str):
                        # Remove any whitespace and convert
                        clean_ain1 = raw_ain1.strip()
                        if clean_ain1:
                            accurate_ain1_value = float(clean_ain1)
                    else:
                        accurate_ain1_value = None
                except (ValueError, TypeError) as e:
                    print(f"Error parsing AIN1 value '{latest_raw_data.ain1}' for device {device.name}: {e}")
                    accurate_ain1_value = None
            
            device_data = {
                'device_id': device.id,
                'device_name': device.name,
                'has_power': power_status.has_power if power_status else False,
                'last_check': power_status.last_check.isoformat() if power_status else None,
                'ain1_value': accurate_ain1_value,  # Use most accurate value from RawData
                'power_loss_detected_at': power_status.power_loss_detected_at.isoformat() if power_status and power_status.power_loss_detected_at else None,
                'last_raw_data_timestamp': latest_raw_data.timestamp.isoformat() if latest_raw_data else None,
                'raw_data_source': 'latest_raw_data' if accurate_ain1_value is not None else 'power_status_fallback'
            }
            
            devices_data.append(device_data)
            
            if not device_data['has_power']:
                devices_without_power += 1
        
        # Prepare summary
        summary = {
            'total_devices': devices.count(),
            'devices_with_power': devices.count() - devices_without_power,
            'devices_without_power': devices_without_power,
            'uptime_percentage': ((devices.count() - devices_without_power) / devices.count() * 100) if devices.count() > 0 else 100
        }
        
        data = {
            'summary': summary,
            'devices': devices_data
        }
        
        return JsonResponse(data, encoder=DjangoJSONEncoder)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_power_data_from_mqtt(request, factory_id):
    """Get power data from PowerData model (updated from counter database)"""
    factory = get_object_or_404(Factory, id=factory_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            permission = PowerManagementPermission.objects.get(user=request.user)
            if not permission.can_access_power_management:
                return JsonResponse({'error': 'Access denied'}, status=403)
        except PowerManagementPermission.DoesNotExist:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    device_id = request.GET.get('device_id', 'all')
    
    # Use unified power management service
    from mill.services.unified_power_management_service import UnifiedPowerManagementService
    service = UnifiedPowerManagementService()
    
    # Get power summary
    summary = service.get_device_power_summary(device_id, factory_id)
    
    # Get power events summary
    events_summary = service.get_power_events_summary(device_id, factory_id, days=1)
    
    # Combine data
    response_data = {
        'summary': {
            'total_devices': summary['total_devices'],
            'devices_with_power': summary['devices_with_power'],
            'devices_without_power': summary['devices_without_power'],
            'power_events_today': summary['power_events_today'],
            'unresolved_events': summary['unresolved_events'],
            'avg_uptime_today': summary['avg_uptime_today'],
            'total_power_consumption': summary['total_power_consumption'],
            'power_loss_events_today': events_summary['power_loss_events'],
            'power_restored_events_today': events_summary['power_restored_events'],
        },
        'devices': summary['devices_data'],
        'recent_events': events_summary['recent_events'],
        'data_source': 'unified_power_management'
    }
    
    return JsonResponse(response_data)