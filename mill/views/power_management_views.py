from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from mill.models import (
    Device, PowerEvent, DevicePowerStatus, PowerNotificationSettings,
    Factory, UserProfile
)
from mill.services.power_management_service import PowerManagementService
from mill.utils.permmissions_handler_utils import is_allowed_factory

@login_required
def power_dashboard(request):
    """Power management dashboard - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        # Get power management service
        power_service = PowerManagementService()
        
        # Get summary statistics
        summary = power_service.get_power_events_summary()
        
        # Get active power events
        active_events = power_service.get_active_power_events()
        
        # Get devices with power issues
        devices_with_issues = DevicePowerStatus.objects.filter(has_power=False)
        
        # Get all factories for super admin
        factories = Factory.objects.all()
        
        # Paginate active events
        paginator = Paginator(active_events, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'summary': summary,
            'active_events': page_obj,
            'devices_with_issues': devices_with_issues,
            'factories': factories,
        }
        
        return render(request, 'mill/power_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power dashboard: {str(e)}')
        return redirect('dashboard')

@login_required
def power_events_list(request):
    """List all power events - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        # Get all power events
        events = PowerEvent.objects.all()
        
        # Filter by device if specified
        device_id = request.GET.get('device')
        if device_id:
            events = events.filter(device_id=device_id)
        
        # Filter by event type if specified
        event_type = request.GET.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)
        
        # Filter by severity if specified
        severity = request.GET.get('severity')
        if severity:
            events = events.filter(severity=severity)
        
        # Filter by resolved status if specified
        resolved = request.GET.get('resolved')
        if resolved is not None:
            is_resolved = resolved.lower() == 'true'
            events = events.filter(is_resolved=is_resolved)
        
        # Order by creation date (newest first)
        events = events.order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(events, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get filter options
        devices = Device.objects.all()
        
        context = {
            'events': page_obj,
            'devices': devices,
            'event_types': PowerEvent.EVENT_TYPES,
            'severity_levels': PowerEvent.SEVERITY_LEVELS,
        }
        
        return render(request, 'mill/power_events_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power events: {str(e)}')
        return redirect('power_dashboard')

@login_required
def power_event_detail(request, event_id):
    """View details of a specific power event - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        event = get_object_or_404(PowerEvent, id=event_id)
        
        context = {
            'event': event,
        }
        
        return render(request, 'mill/power_event_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power event: {str(e)}')
        return redirect('power_events_list')

@login_required
def resolve_power_event(request, event_id):
    """Mark a power event as resolved - Super admin only"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    try:
        event = get_object_or_404(PowerEvent, id=event_id)
        
        if request.method == 'POST':
            notes = request.POST.get('notes', '')
            event.mark_as_resolved(request.user, notes)
            
            messages.success(request, f'Power event "{event.get_event_type_display()}" has been resolved.')
            return JsonResponse({'success': True, 'message': 'Event resolved successfully'})
        
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def device_power_status(request, device_id):
    """View power status for a specific device - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        device = get_object_or_404(Device, id=device_id)
        
        # Get power status
        power_status = DevicePowerStatus.objects.filter(device=device).first()
        
        # Get power events for this device
        power_events = PowerEvent.objects.filter(device=device).order_by('-created_at')[:10]
        
        context = {
            'device': device,
            'power_status': power_status,
            'power_events': power_events,
        }
        
        return render(request, 'mill/device_power_status.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading device power status: {str(e)}')
        return redirect('power_dashboard')

@login_required
def power_notification_settings(request):
    """Manage power notification settings - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        # Get or create user's power notification settings
        settings, created = PowerNotificationSettings.objects.get_or_create(
            user=request.user,
            defaults={
                'notify_power_loss': True,
                'notify_power_restore': True,
                'notify_production_without_power': True,
                'email_power_loss': True,
                'email_production_without_power': True,
            }
        )
        
        if request.method == 'POST':
            # Update notification preferences
            settings.notify_power_loss = request.POST.get('notify_power_loss') == 'on'
            settings.notify_power_restore = request.POST.get('notify_power_restore') == 'on'
            settings.notify_production_without_power = request.POST.get('notify_production_without_power') == 'on'
            settings.notify_power_fluctuation = request.POST.get('notify_power_fluctuation') == 'on'
            
            # Update email preferences
            settings.email_power_loss = request.POST.get('email_power_loss') == 'on'
            settings.email_power_restore = request.POST.get('email_power_restore') == 'on'
            settings.email_production_without_power = request.POST.get('email_production_without_power') == 'on'
            settings.email_power_fluctuation = request.POST.get('email_power_fluctuation') == 'on'
            
            # Update notification frequency
            settings.notification_frequency = request.POST.get('notification_frequency', 'immediate')
            
            # Update responsible devices
            device_ids = request.POST.getlist('responsible_devices')
            settings.responsible_devices.set(device_ids)
            
            settings.save()
            messages.success(request, 'Power notification settings updated successfully.')
            return redirect('power_notification_settings')
        
        # Get available devices
        available_devices = Device.objects.all()
        
        context = {
            'settings': settings,
            'available_devices': available_devices,
        }
        
        return render(request, 'mill/power_notification_settings.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power notification settings: {str(e)}')
        return redirect('power_dashboard')

@login_required
def power_analytics(request):
    """Power analytics and statistics - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        # Get power management service
        power_service = PowerManagementService()
        
        # Get summary statistics
        summary = power_service.get_power_events_summary()
        
        # Get power events by type
        events_by_type = {}
        for event_type, _ in PowerEvent.EVENT_TYPES:
            count = PowerEvent.objects.filter(event_type=event_type).count()
            events_by_type[event_type] = count
        
        # Get power events by severity
        events_by_severity = {}
        for severity, _ in PowerEvent.SEVERITY_LEVELS:
            count = PowerEvent.objects.filter(severity=severity).count()
            events_by_severity[severity] = count
        
        # Get devices with power issues
        devices_with_issues = DevicePowerStatus.objects.filter(has_power=False).count()
        total_devices = Device.objects.count()
        
        # Get recent power events (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_events = PowerEvent.objects.filter(created_at__gte=thirty_days_ago).count()
        
        context = {
            'summary': summary,
            'events_by_type': events_by_type,
            'events_by_severity': events_by_severity,
            'devices_with_issues': devices_with_issues,
            'total_devices': total_devices,
            'recent_events': recent_events,
        }
        
        return render(request, 'mill/power_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power analytics: {str(e)}')
        return redirect('power_dashboard')

@login_required
def power_status_api(request, factory_id):
    """API endpoint to get power status for devices in a factory"""
    try:
        # Check permissions
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    return JsonResponse({'error': 'Permission denied'}, status=403)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Get devices for this factory
        devices = Device.objects.filter(factory=factory)
        
        # Get power status for each device
        power_status_data = []
        for device in devices:
            power_status = DevicePowerStatus.objects.filter(device=device).first()
            
            if power_status:
                power_status_data.append({
                    'device_id': device.id,
                    'device_name': device.name,
                    'has_power': power_status.has_power,
                    'ain1_value': power_status.ain1_value,
                    'last_check': power_status.last_power_check.isoformat() if power_status.last_power_check else None,
                    'power_loss_detected_at': power_status.power_loss_detected_at.isoformat() if power_status.power_loss_detected_at else None,
                    'production_during_power_loss': power_status.production_during_power_loss,
                })
            else:
                # Create power status if it doesn't exist
                power_status = DevicePowerStatus.objects.create(
                    device=device,
                    has_power=True,
                    power_threshold=0.0
                )
                power_status_data.append({
                    'device_id': device.id,
                    'device_name': device.name,
                    'has_power': True,
                    'ain1_value': None,
                    'last_check': None,
                    'power_loss_detected_at': None,
                    'production_during_power_loss': False,
                })
        
        # Get summary statistics
        total_devices = len(devices)
        devices_with_power = sum(1 for status in power_status_data if status['has_power'])
        devices_without_power = total_devices - devices_with_power
        
        # Get recent power events (last 24 hours)
        yesterday = timezone.now() - timezone.timedelta(days=1)
        recent_events = PowerEvent.objects.filter(
            device__factory=factory,
            created_at__gte=yesterday
        ).count()
        
        return JsonResponse({
            'factory_id': factory_id,
            'factory_name': factory.name,
            'devices': power_status_data,
            'summary': {
                'total_devices': total_devices,
                'devices_with_power': devices_with_power,
                'devices_without_power': devices_without_power,
                'recent_events_24h': recent_events,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500) 