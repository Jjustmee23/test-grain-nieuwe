from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from mill.models import Device, DoorOpenLogs, RawData
from django.db.models import Q

@login_required
def door_history(request, device_id):
    """Display simple door history for a specific device"""
    device = get_object_or_404(Device, id=device_id)
    
    # Get date range filter
    days_filter = request.GET.get('days', '7')
    try:
        days = int(days_filter)
    except ValueError:
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get door history
    door_logs = DoorOpenLogs.objects.filter(
        device=device,
        timestamp__gte=start_date
    ).order_by('-timestamp')
    
    # Calculate statistics
    total_opens = door_logs.count()
    resolved_logs = door_logs.filter(is_resolved=True)
    total_duration = sum((log.resolved_at - log.timestamp).total_seconds() / 60 for log in resolved_logs if log.resolved_at)
    avg_duration = total_duration / resolved_logs.count() if resolved_logs.count() > 0 else 0
    
    # Get today's opens
    today = timezone.now().date()
    today_opens = door_logs.filter(timestamp__date=today).count()
    
    context = {
        'device': device,
        'door_logs': door_logs,
        'total_opens': total_opens,
        'total_duration': total_duration,
        'avg_duration': avg_duration,
        'today_opens': today_opens,
        'selected_days': days,
        'days_options': [1, 3, 7, 14, 30]
    }
    
    return render(request, 'mill/door_history.html', context)

@login_required
def all_doors_history(request):
    """Display door history for all devices"""
    # Get date range filter
    days_filter = request.GET.get('days', '7')
    try:
        days = int(days_filter)
    except ValueError:
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get all door logs
    door_logs = DoorOpenLogs.objects.filter(
        timestamp__gte=start_date
    ).select_related('device', 'device__factory').order_by('-timestamp')
    
    # Group by device
    devices_data = {}
    for log in door_logs:
        device_id = log.device.id
        if device_id not in devices_data:
            devices_data[device_id] = {
                'device': log.device,
                'logs': [],
                'total_opens': 0,
                'total_duration': 0
            }
        
        devices_data[device_id]['logs'].append(log)
        devices_data[device_id]['total_opens'] += 1
        if log.is_resolved and log.resolved_at:
            devices_data[device_id]['total_duration'] += (log.resolved_at - log.timestamp).total_seconds() / 60
    
    # Calculate averages
    for device_data in devices_data.values():
        if device_data['total_opens'] > 0:
            device_data['avg_duration'] = device_data['total_duration'] / device_data['total_opens']
        else:
            device_data['avg_duration'] = 0
    
    context = {
        'devices_data': list(devices_data.values()),
        'selected_days': days,
        'days_options': [1, 3, 7, 14, 30],
        'total_events': door_logs.count()
    }
    
    return render(request, 'mill/all_doors_history.html', context)

@login_required
def door_history_modal_api(request, factory_id):
    """API endpoint for door history modal data"""
    try:
        # Get devices for this factory
        devices = Device.objects.filter(factory_id=factory_id)
        
        # Get recent door logs for all devices in this factory
        door_logs = DoorOpenLogs.objects.filter(
            device__factory_id=factory_id
        ).select_related('device').order_by('-timestamp')[:20]
        
        # Calculate current door status
        open_doors = 0
        total_doors = devices.count()
        
        # Get current door status from latest RawData
        for device in devices:
            latest_raw_data = RawData.objects.filter(
                device=device,
                din__isnull=False
            ).exclude(din='').order_by('-timestamp').first()
            
            if latest_raw_data:
                try:
                    import json
                    din_data = json.loads(latest_raw_data.din) if isinstance(latest_raw_data.din, str) else latest_raw_data.din
                    door_input_index = 3
                    
                    if isinstance(din_data, list) and len(din_data) > door_input_index:
                        if din_data[door_input_index] == 1:
                            open_doors += 1
                except:
                    pass
        
        # Format logs for modal
        logs_data = []
        for log in door_logs:
            logs_data.append({
                'timestamp': log.timestamp.isoformat(),
                'device_name': log.device.name,
                'din_data': log.din_data,
                'door_input_index': log.door_input_index,
                'is_resolved': log.is_resolved,
                'resolved_at': log.resolved_at.isoformat() if log.resolved_at else None,
                'duration_minutes': (log.resolved_at - log.timestamp).total_seconds() / 60 if log.resolved_at and log.timestamp else None
            })
        
        return JsonResponse({
            'total_doors': total_doors,
            'open_doors': open_doors,
            'closed_doors': total_doors - open_doors,
            'recent_logs': logs_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500) 