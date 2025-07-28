from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from mill.models import (
    Device, PowerEvent, DevicePowerStatus, PowerNotificationSettings,
    Factory, UserProfile, PowerManagementPermission
)
from mill.services.unified_power_management_service import UnifiedPowerManagementService
from mill.services.counter_sync_service import CounterSyncService
from mill.services.power_management_service import PowerManagementService
from mill.utils.permmissions_handler_utils import is_allowed_factory
from mill.models import PowerData

@login_required
def power_dashboard(request):
    """Power management dashboard - Super admin or authorized users only"""
    if not request.user.is_superuser and not PowerManagementPermission.has_power_access(request.user):
        messages.error(request, 'Access denied. Power management is only available for authorized users.')
        return redirect('dashboard')
    
    try:
        # Get unified power management service
        service = UnifiedPowerManagementService()
        
        # Get power summary
        power_summary = service.get_device_power_summary()
        
        # Get power events summary
        events_summary = service.get_power_events_summary(days=30)
        
        # Get power analytics
        analytics = service.get_power_analytics(days=30)
        
        # Get all factories for super admin
        factories = Factory.objects.all()
        
        # Get devices with power issues
        devices_with_issues = DevicePowerStatus.objects.filter(has_power=False).select_related('device', 'device__factory')
        
        # Paginate recent events
        recent_events = PowerEvent.objects.filter(is_resolved=False).order_by('-created_at')
        paginator = Paginator(recent_events, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'power_summary': power_summary,
            'events_summary': events_summary,
            'analytics': analytics,
            'active_events': page_obj,
            'factories': factories,
            'devices_with_issues': devices_with_issues,
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
        
        # Get or create power status
        power_status, created = DevicePowerStatus.objects.get_or_create(
            device=device,
            defaults={'power_threshold': 0.0}
        )
        
        # If created, update with latest data
        if created:
            from mill.models import RawData
            latest_raw_data = RawData.objects.filter(
                device=device,
                ain1_value__isnull=False
            ).order_by('-timestamp').first()
            
            if latest_raw_data:
                power_status.ain1_value = latest_raw_data.ain1_value
                power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
                power_status.has_power = latest_raw_data.ain1_value > 0
                power_status.save()
        
        # Get power events for this device
        power_events = PowerEvent.objects.filter(device=device).order_by('-created_at')[:10]
        
        # Get counter changes data
        power_service = UnifiedPowerManagementService()
        hours = int(request.GET.get('hours', 24))
        counter_data = power_service.get_device_counter_changes(device, hours=hours)
        
        context = {
            'device': device,
            'power_status': power_status,
            'power_events': power_events,
            'counter_data': counter_data,
            'selected_hours': hours,
        }
        
        return render(request, 'mill/device_power_status.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading device power status: {str(e)}')
        return redirect('power_dashboard')

@login_required
def device_suspicious_activity(request, device_id):
    """View suspicious activity analysis for a specific device - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Power management is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        device = get_object_or_404(Device, id=device_id)
        
        # Get or create power status
        power_status, created = DevicePowerStatus.objects.get_or_create(
            device=device,
            defaults={'power_threshold': 0.0}
        )
        
        # If created, update with latest data
        if created:
            from mill.models import RawData
            latest_raw_data = RawData.objects.filter(
                device=device,
                ain1_value__isnull=False
            ).order_by('-timestamp').first()
            
            if latest_raw_data:
                power_status.ain1_value = latest_raw_data.ain1_value
                power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
                power_status.has_power = latest_raw_data.ain1_value > 0
                power_status.save()
        
        # Get suspicious activity analysis
        power_service = UnifiedPowerManagementService() # Changed from PowerManagementService to UnifiedPowerManagementService
        check_interval = int(request.GET.get('check_interval', 5))  # Default 5 minutes
        suspicious_analysis = power_service.get_suspicious_activity_analysis(device, check_interval)
        
        # Get recent power events for context
        power_events = PowerEvent.objects.filter(device=device).order_by('-created_at')[:5]
        
        context = {
            'device': device,
            'power_status': power_status,
            'suspicious_analysis': suspicious_analysis,
            'power_events': power_events,
            'check_interval': check_interval,
        }
        
        return render(request, 'mill/device_suspicious_activity.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading suspicious activity analysis: {str(e)}')
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
        power_service = UnifiedPowerManagementService()
        
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
        total_devices = Device.objects.filter(factory__isnull=False).count()
        
        # Get recent power events (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_events = PowerEvent.objects.filter(created_at__gte=thirty_days_ago).count()
        
        # Calculate uptime percentage
        devices_with_power = DevicePowerStatus.objects.filter(
            device__factory__isnull=False, 
            has_power=True
        ).count()
        uptime_percentage = (devices_with_power / total_devices * 100) if total_devices > 0 else 100
        
        # Calculate real power consumption trends from database
        avg_power_consumption = 0
        peak_power_usage = 0
        power_efficiency_score = 85.5  # Default score
        energy_cost_savings = 1250.75  # Default savings
        
        # Get power consumption data from all devices
        all_power_values = []
        devices_with_data = 0
        
        for device in Device.objects.filter(factory__isnull=False):
            power_data = power_service.get_power_consumption_data(device, days=30)
            if power_data:
                power_values = [data['ain1_value'] for data in power_data if data['ain1_value'] > 0]
                if power_values:
                    all_power_values.extend(power_values)
                    devices_with_data += 1
        
        if all_power_values:
            avg_power_consumption = sum(all_power_values) / len(all_power_values)
            peak_power_usage = max(all_power_values)
            
            # Calculate efficiency score based on uptime and power consistency
            power_efficiency_score = min(100, uptime_percentage + 15)  # Base score on uptime
        
        # Trends analysis (simulated data)
        events_trend_count = PowerEvent.objects.filter(created_at__gte=thirty_days_ago).count()
        events_trend_direction = 'down' if events_trend_count < 10 else 'up'
        events_trend_percentage = 15.5
        
        consumption_trend_value = 12.8
        consumption_trend_direction = 'down'
        consumption_trend_percentage = 8.2
        
        uptime_trend_value = 92.5
        uptime_trend_direction = 'up'
        uptime_trend_percentage = 5.3
        
        efficiency_trend_value = 87.2
        efficiency_trend_direction = 'up'
        efficiency_trend_percentage = 12.1
        
        context = {
            'summary': summary,
            'events_by_type': events_by_type,
            'events_by_severity': events_by_severity,
            'devices_with_issues': devices_with_issues,
            'total_devices': total_devices,
            'recent_events': recent_events,
            'uptime_percentage': uptime_percentage,
            'avg_power_consumption': avg_power_consumption,
            'peak_power_usage': peak_power_usage,
            'power_efficiency_score': power_efficiency_score,
            'energy_cost_savings': energy_cost_savings,
            'events_trend_count': events_trend_count,
            'events_trend_direction': events_trend_direction,
            'events_trend_percentage': events_trend_percentage,
            'consumption_trend_value': consumption_trend_value,
            'consumption_trend_direction': consumption_trend_direction,
            'consumption_trend_percentage': consumption_trend_percentage,
            'uptime_trend_value': uptime_trend_value,
            'uptime_trend_direction': uptime_trend_direction,
            'uptime_trend_percentage': uptime_trend_percentage,
            'efficiency_trend_value': efficiency_trend_value,
            'efficiency_trend_direction': efficiency_trend_direction,
            'efficiency_trend_percentage': efficiency_trend_percentage,
        }
        
        return render(request, 'mill/power_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power analytics: {str(e)}')
        return redirect('power_dashboard')

@login_required
def power_status_api(request, factory_id):
    """API endpoint to get power status for devices in a factory"""
    try:
        # Check permissions - super admin or authorized users with power status access
        if not request.user.is_superuser and not PowerManagementPermission.has_power_status_access(request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Additional factory access check for non-super users
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    return JsonResponse({'error': 'Permission denied'}, status=403)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Use unified power management service
        service = UnifiedPowerManagementService()
        
        # Get power summary for this factory
        power_summary = service.get_device_power_summary(factory_id=factory_id)
        
        # Get power events summary for this factory
        events_summary = service.get_power_events_summary(factory_id=factory_id, days=1)
        
        # Convert devices data to expected format
        devices_data = []
        for device_data in power_summary['devices_data']:
            devices_data.append({
                'device_id': device_data['device_id'],
                'device_name': device_data['device_name'],
                'has_power': device_data['has_power'],
                'ain1_value': device_data['ain1_value'],
                'last_update': device_data['last_update'].isoformat() if device_data['last_update'] else None,
                'power_loss_detected_at': device_data['last_power_loss'].isoformat() if device_data['last_power_loss'] else None,
                'uptime_percentage': device_data['uptime_percentage'],
                'power_loss_count_today': device_data['power_loss_count_today'],
                'power_restore_count_today': device_data['power_restore_count_today'],
            })
        
        return JsonResponse({
            'factory_id': factory_id,
            'factory_name': factory.name,
            'devices': devices_data,
            'summary': {
                'total_devices': power_summary['total_devices'],
                'devices_with_power': power_summary['devices_with_power'],
                'devices_without_power': power_summary['devices_without_power'],
                'avg_uptime_today': power_summary['avg_uptime_today'],
                'total_power_consumption': power_summary['total_power_consumption'],
                'power_events_today': power_summary['power_events_today'],
                'unresolved_events': power_summary['unresolved_events'],
                'recent_events_24h': events_summary['total_events'],
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def factory_power_events(request, factory_id):
    """List power events for a specific factory"""
    try:
        # Check permissions
        if not request.user.is_superuser and not PowerManagementPermission.has_power_status_access(request.user):
            messages.error(request, 'Access denied. Power management is only available for authorized users.')
            return redirect('dashboard')
        
        # Additional factory access check for non-super users
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    messages.error(request, 'Access denied to this factory.')
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Get power events for devices in this factory
        events = PowerEvent.objects.filter(device__factory=factory)
        
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
        
        # Get devices for this factory
        devices = Device.objects.filter(factory=factory)
        
        context = {
            'factory': factory,
            'events': page_obj,
            'devices': devices,
            'event_types': PowerEvent.EVENT_TYPES,
            'severity_levels': PowerEvent.SEVERITY_LEVELS,
        }
        
        return render(request, 'mill/factory_power_events.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power events: {str(e)}')
        return redirect('view_statistics', factory_id=factory_id)

@login_required
def factory_power_analytics(request, factory_id):
    """Power analytics for a specific factory"""
    try:
        # Check permissions
        if not request.user.is_superuser and not PowerManagementPermission.has_power_status_access(request.user):
            messages.error(request, 'Access denied. Power management is only available for authorized users.')
            return redirect('dashboard')
        
        # Additional factory access check for non-super users
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    messages.error(request, 'Access denied to this factory.')
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Get power management service
        power_service = UnifiedPowerManagementService()
        
        # Get devices for this factory
        devices = Device.objects.filter(factory=factory)
        
        # Get power events for this factory
        factory_events = PowerEvent.objects.filter(device__factory=factory)
        
        # Get summary statistics for this factory
        total_devices = devices.count()
        devices_with_power = DevicePowerStatus.objects.filter(
            device__factory=factory, 
            has_power=True
        ).count()
        devices_without_power = total_devices - devices_with_power
        
        # Calculate uptime percentage for this factory
        uptime_percentage = (devices_with_power / total_devices * 100) if total_devices > 0 else 100
        
        # Get power events by type for this factory
        events_by_type = {}
        for event_type, _ in PowerEvent.EVENT_TYPES:
            count = factory_events.filter(event_type=event_type).count()
            events_by_type[event_type] = count
        
        # Get power events by severity for this factory
        events_by_severity = {}
        for severity, _ in PowerEvent.SEVERITY_LEVELS:
            count = factory_events.filter(severity=severity).count()
            events_by_severity[severity] = count
        
        # Get recent power events (last 30 days) for this factory
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_events = factory_events.filter(created_at__gte=thirty_days_ago).count()
        
        # Calculate power consumption for this factory
        avg_power_consumption = 0
        peak_power_usage = 0
        all_power_values = []
        
        for device in devices:
            power_data = power_service.get_power_consumption_data(device, days=30)
            if power_data:
                power_values = [data['ain1_value'] for data in power_data if data['ain1_value'] > 0]
                if power_values:
                    all_power_values.extend(power_values)
        
        if all_power_values:
            avg_power_consumption = sum(all_power_values) / len(all_power_values)
            peak_power_usage = max(all_power_values)
        
        # Calculate efficiency score for this factory
        power_efficiency_score = min(100, uptime_percentage + 15)
        
        # Trends analysis for this factory
        events_trend_count = factory_events.filter(created_at__gte=thirty_days_ago).count()
        events_trend_direction = 'down' if events_trend_count < 5 else 'up'
        events_trend_percentage = 15.5
        
        consumption_trend_value = 12.8
        consumption_trend_direction = 'down'
        consumption_trend_percentage = 8.2
        
        uptime_trend_value = uptime_percentage
        uptime_trend_direction = 'up' if uptime_percentage > 90 else 'down'
        uptime_trend_percentage = 5.3
        
        efficiency_trend_value = power_efficiency_score
        efficiency_trend_direction = 'up'
        efficiency_trend_percentage = 12.1
        
        # Get factory statistics data (similar to view_statistics)
        from mill.models import ProductionData
        from datetime import datetime
        
        # Get current date
        current_date = timezone.now().date()
        
        # Calculate factory totals
        factory_total = {
            'daily_total': 0,
            'weekly_total': 0,
            'monthly_total': 0,
            'yearly_total': 0
        }
        
        # Get production data for this factory's devices
        production_data = ProductionData.objects.filter(
            device__factory=factory,
            created_at__date=current_date
        ).select_related('device')
        
        # Calculate totals
        for production in production_data:
            factory_total['daily_total'] += production.daily_production or 0
            factory_total['weekly_total'] += production.weekly_production or 0
            factory_total['monthly_total'] += production.monthly_production or 0
            factory_total['yearly_total'] += production.yearly_production or 0
        
        # Get previous year total (simplified)
        yearly_previous = 0  # This would need to be calculated from historical data
        
        context = {
            'factory': factory,
            'total_devices': total_devices,
            'devices_with_power': devices_with_power,
            'devices_without_power': devices_without_power,
            'uptime_percentage': uptime_percentage,
            'events_by_type': events_by_type,
            'events_by_severity': events_by_severity,
            'recent_events': recent_events,
            'avg_power_consumption': avg_power_consumption,
            'peak_power_usage': peak_power_usage,
            'power_efficiency_score': power_efficiency_score,
            'events_trend_count': events_trend_count,
            'events_trend_direction': events_trend_direction,
            'events_trend_percentage': events_trend_percentage,
            'consumption_trend_value': consumption_trend_value,
            'consumption_trend_direction': consumption_trend_direction,
            'consumption_trend_percentage': consumption_trend_percentage,
            'uptime_trend_value': uptime_trend_value,
            'uptime_trend_direction': uptime_trend_direction,
            'uptime_trend_percentage': uptime_trend_percentage,
            'efficiency_trend_value': efficiency_trend_value,
            'efficiency_trend_direction': efficiency_trend_direction,
            'efficiency_trend_percentage': efficiency_trend_percentage,
            # Add factory statistics
            'factory_total': factory_total,
            'yearly_previous': yearly_previous,
        }
        
        return render(request, 'mill/factory_power_analytics.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading power analytics: {str(e)}')
        return redirect('view_statistics', factory_id=factory_id)

@login_required
def factory_power_overview(request, factory_id):
    """Power overview for a specific factory - shows all power statistics"""
    try:
        # Check permissions
        if not request.user.is_superuser and not PowerManagementPermission.has_power_status_access(request.user):
            messages.error(request, 'Access denied. Power management is only available for authorized users.')
            return redirect('dashboard')
        
        # Additional factory access check for non-super users
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    messages.error(request, 'Access denied to this factory.')
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, 'Access denied.')
                return redirect('dashboard')
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Get unified power management service
        service = UnifiedPowerManagementService()
        
        # Get devices for this factory
        devices = Device.objects.filter(factory=factory)
        
        # Ensure all devices have DevicePowerStatus records
        for device in devices:
            power_status, created = DevicePowerStatus.objects.get_or_create(
                device=device,
                defaults={'power_threshold': 0.0}
            )
            
            # If created, update with latest data
            if created:
                from mill.models import RawData
                latest_raw_data = RawData.objects.filter(
                    device=device,
                    ain1_value__isnull=False
                ).order_by('-timestamp').first()
                
                if latest_raw_data:
                    power_status.ain1_value = latest_raw_data.ain1_value
                    power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
                    power_status.has_power = latest_raw_data.ain1_value > 0
                    power_status.save()
        
        # Get power summary for this factory
        power_summary = service.get_device_power_summary(factory_id=factory_id)
        
        # Get power events summary for this factory
        events_summary = service.get_power_events_summary(factory_id=factory_id, days=30)
        
        # Get power analytics for this factory
        analytics = service.get_power_analytics(factory_id=factory_id, days=30)
        
        # Get actual DevicePowerStatus objects for all devices
        power_statuses = []
        for device in devices:
            power_status = DevicePowerStatus.objects.filter(device=device).first()
            if power_status:
                power_statuses.append(power_status)
            else:
                # This shouldn't happen since we created them above, but just in case
                power_status, created = DevicePowerStatus.objects.get_or_create(
                    device=device,
                    defaults={'power_threshold': 0.0}
                )
                power_statuses.append(power_status)
        
        # Get recent power events (last 24 hours)
        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        recent_events = PowerEvent.objects.filter(
            device__factory=factory,
            created_at__gte=twenty_four_hours_ago
        ).select_related('device').order_by('-created_at')[:10]
        
        # Get unresolved power events
        unresolved_events = PowerEvent.objects.filter(
            device__factory=factory,
            is_resolved=False
        ).select_related('device').order_by('-created_at')[:5]
        
        # Ensure we have valid summary data
        if not power_summary or power_summary['total_devices'] == 0:
            # Create default summary for factory with no devices
            power_summary = {
                'total_devices': devices.count(),
                'devices_with_power': 0,
                'devices_without_power': devices.count(),
                'power_events_today': 0,
                'unresolved_events': 0,
                'avg_uptime_today': 0.0,
                'total_power_consumption': 0.0,
                'devices_data': []
            }
        
        # Debug: Print power statuses to console
        print(f"DEBUG: Factory {factory.name} power statuses:")
        for ps in power_statuses:
            print(f"  - {ps.device.name}: last_check={ps.last_power_check}, has_power={ps.has_power}, ain1={ps.ain1_value}")
        
        context = {
            'factory': factory,
            'power_summary': power_summary,
            'events_summary': events_summary,
            'analytics': analytics,
            'power_statuses': power_statuses,
            'recent_events': recent_events,
            'unresolved_events': unresolved_events,
            'total_devices': power_summary['total_devices'],
            'devices_with_power': power_summary['devices_with_power'],
            'devices_without_power': power_summary['devices_without_power'],
            'uptime_percentage': power_summary['avg_uptime_today'],
            'avg_power_consumption': analytics['trends'].get('avg_power_consumption', 0) if analytics['trends'] else 0,
            'peak_power_usage': analytics['trends'].get('max_power_consumption', 0) if analytics['trends'] else 0,
            'total_power_consumption': power_summary['total_power_consumption'],
            'power_events_today': power_summary['power_events_today'],
            'unresolved_events_count': power_summary['unresolved_events'],
        }
        

        
        return render(request, 'mill/factory_power_overview.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading factory power overview: {str(e)}')
        return redirect('view_statistics', factory_id=factory_id)

@login_required
def sync_counter_data(request):
    """Sync data from counter database and update power management - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Data synchronization is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        sync_service = CounterSyncService()
        power_service = UnifiedPowerManagementService()
        
        # Get counter database status
        status = sync_service.get_counter_db_status()
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'sync_latest':
                # Sync latest data
                synced_count = sync_service.sync_latest_data()
                messages.success(request, f'Successfully synced {synced_count} records from counter database.')
                
            elif action == 'sync_historical':
                # Sync historical data
                days = int(request.POST.get('days', 7))
                synced_count = sync_service.sync_historical_data(days=days)
                messages.success(request, f'Successfully synced {synced_count} historical records from counter database.')
                
            elif action == 'update_power':
                # Update power status using unified service
                result = power_service.update_all_devices_power_status()
                messages.success(request, f'Successfully updated power status: {result["updated_count"]} devices updated, {result["error_count"]} errors.')
                
            elif action == 'full_sync':
                # Full sync and power update
                synced_count = sync_service.sync_latest_data()
                result = power_service.update_all_devices_power_status()
                messages.success(request, f'Full sync completed: {synced_count} records synced, {result["updated_count"]} devices updated.')
            
            return redirect('sync_counter_data')
        
        # Get power management summary
        power_summary = power_service.get_device_power_summary()
        events_summary = power_service.get_power_events_summary(days=30)
        
        context = {
            'counter_status': status,
            'power_summary': power_summary,
            'events_summary': events_summary,
        }
        
        return render(request, 'mill/sync_counter_data.html', context)
        
    except Exception as e:
        messages.error(request, f'Error during data synchronization: {str(e)}')
        return redirect('dashboard') 

@login_required
def power_data_mqtt_api(request, factory_id):
    """API endpoint to get unified power management data for devices in a factory"""
    try:
        # Check permissions - super admin or authorized users with power status access
        if not request.user.is_superuser and not PowerManagementPermission.has_power_status_access(request.user):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Additional factory access check for non-super users
        if not request.user.is_superuser:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if not user_profile.allowed_factories.filter(id=factory_id).exists():
                    return JsonResponse({'error': 'Permission denied'}, status=403)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get factory
        factory = get_object_or_404(Factory, id=factory_id)
        
        # Get device filter
        device_id = request.GET.get('device_id', 'all')
        
        # Use unified power management service
        service = UnifiedPowerManagementService()
        
        # Get power summary for this factory
        power_summary = service.get_device_power_summary(factory_id=factory_id)
        
        # Get power events summary for this factory
        events_summary = service.get_power_events_summary(factory_id=factory_id, days=1)
        
        # Get recent power events
        recent_events = service.get_recent_power_events(factory_id=factory_id, limit=5)
        
        # Convert devices data to expected format
        devices_data = []
        for device_data in power_summary['devices_data']:
            # Filter by specific device if requested
            if device_id != 'all' and str(device_data['device_id']) != str(device_id):
                continue
                
            devices_data.append({
                'device_id': device_data['device_id'],
                'device_name': device_data['device_name'],
                'has_power': device_data['has_power'],
                'ain1_value': device_data['ain1_value'],
                'last_update': device_data['last_update'].isoformat() if device_data['last_update'] else None,
                'last_power_loss': device_data['last_power_loss'].isoformat() if device_data['last_power_loss'] else None,
                'last_power_restore': device_data['last_power_restore'].isoformat() if device_data['last_power_restore'] else None,
                'uptime_percentage': device_data['uptime_percentage'],
                'power_loss_count_today': device_data['power_loss_count_today'],
                'power_restore_count_today': device_data['power_restore_count_today'],
                'power_threshold': device_data.get('power_threshold', 0.0),
            })
        
        # Convert recent events to expected format
        events_data = []
        for event in recent_events:
            events_data.append({
                'id': event.id,
                'device_name': event.device.name,
                'event_type': event.event_type,
                'message': event.message,
                'created_at': event.created_at.isoformat(),
                'severity': event.severity,
                'is_resolved': event.is_resolved,
            })
        
        return JsonResponse({
            'factory_id': factory_id,
            'factory_name': factory.name,
            'device_id': device_id,
            'summary': {
                'total_devices': power_summary['total_devices'],
                'devices_with_power': power_summary['devices_with_power'],
                'devices_without_power': power_summary['devices_without_power'],
                'avg_uptime_today': power_summary['avg_uptime_today'],
                'total_power_consumption': power_summary['total_power_consumption'],
                'power_events_today': power_summary['power_events_today'],
                'unresolved_events': power_summary['unresolved_events'],
                'recent_events_24h': events_summary['total_events'],
            },
            'devices': devices_data,
            'recent_events': events_data,
            'data_source': 'unified_power_management',
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500) 

@login_required
def all_devices_without_power(request):
    """Super admin view: Show all devices currently without power"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. This page is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        power_service = UnifiedPowerManagementService()
        devices_without_power = power_service.get_all_devices_without_power()
        
        # Calculate summary statistics
        total_devices = len(devices_without_power)
        critical_devices = len([d for d in devices_without_power if d['severity'] == 'critical'])
        warning_devices = len([d for d in devices_without_power if d['severity'] == 'warning'])
        
        total_production_without_power = sum(
            d['detailed_analysis'].get('statistics', {}).get('total_production_without_power', 0)
            for d in devices_without_power
        )
        
        context = {
            'devices_without_power': devices_without_power,
            'summary': {
                'total_devices': total_devices,
                'critical_devices': critical_devices,
                'warning_devices': warning_devices,
                'total_production_without_power': total_production_without_power
            }
        }
        
        return render(request, 'mill/all_devices_without_power.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading devices without power: {str(e)}')
        return redirect('power_dashboard')

@login_required
def device_detailed_power_analysis(request, device_id):
    """Detailed power analysis for a specific device - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. This page is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        device = get_object_or_404(Device, id=device_id)
        power_service = UnifiedPowerManagementService()
        
        # Get detailed analysis
        analysis = power_service.get_device_detailed_power_analysis(device)
        
        # Get or create power status
        power_status, created = DevicePowerStatus.objects.get_or_create(
            device=device,
            defaults={'power_threshold': 0.0}
        )
        
        # If created, update with latest data
        if created:
            from mill.models import RawData
            latest_raw_data = RawData.objects.filter(
                device=device,
                ain1_value__isnull=False
            ).order_by('-timestamp').first()
            
            if latest_raw_data:
                power_status.ain1_value = latest_raw_data.ain1_value
                power_status.last_power_check = latest_raw_data.timestamp or timezone.now()
                power_status.has_power = latest_raw_data.ain1_value > 0
                power_status.save()
        
        context = {
            'device': device,
            'analysis': analysis,
            'power_status': power_status,
        }
        
        return render(request, 'mill/device_detailed_power_analysis.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading device analysis: {str(e)}')
        return redirect('power_dashboard')

@login_required
def export_device_power_analysis(request, device_id):
    """Export device power analysis to Excel - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. This page is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        from datetime import datetime
        
        device = get_object_or_404(Device, id=device_id)
        power_service = UnifiedPowerManagementService()
        
        # Get detailed analysis
        analysis = power_service.get_device_detailed_power_analysis(device)
        
        if not analysis['has_data']:
            messages.error(request, 'No data available for export')
            return redirect('device_detailed_power_analysis', device_id=device_id)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Device Name',
                    'Factory',
                    'Current Status',
                    'Total Incidents',
                    'Incidents with Counter Activity',
                    'Total Production without Power',
                    'Total Downtime (hours)',
                    'Average Incident Duration (hours)',
                    'Export Date'
                ],
                'Value': [
                    device.name,
                    device.factory.name if device.factory else 'N/A',
                    analysis['current_status'],
                    analysis['statistics']['total_incidents'],
                    analysis['statistics']['incidents_with_counter'],
                    analysis['statistics']['total_production_without_power'],
                    round(analysis['statistics']['total_downtime'].total_seconds() / 3600, 2),
                    round(analysis['statistics']['avg_incident_duration'].total_seconds() / 3600, 2),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Incidents sheet
            if analysis['statistics']['power_incidents']:
                incidents_data = []
                for incident in analysis['statistics']['power_incidents']:
                    incidents_data.append({
                        'Start Time': incident['start_time'].strftime('%Y-%m-%d %H:%M:%S') if incident['start_time'] else 'N/A',
                        'End Time': incident['end_time'].strftime('%Y-%m-%d %H:%M:%S') if incident['end_time'] else 'N/A',
                        'Duration (hours)': round(incident['duration'].total_seconds() / 3600, 2) if 'duration' in incident else 0,
                        'Start Counter': incident['start_counter'],
                        'End Counter': incident['end_counter'] if incident['end_counter'] else 'N/A',
                        'Total Production': incident['total_production'],
                        'Has Counter Activity': 'Yes' if incident['has_counter_activity'] else 'No',
                        'Is Ongoing': 'Yes' if incident.get('is_ongoing', False) else 'No'
                    })
                
                incidents_df = pd.DataFrame(incidents_data)
                incidents_df.to_excel(writer, sheet_name='Power Incidents', index=False)
                
                # Counter changes sheet
                all_counter_changes = []
                for i, incident in enumerate(analysis['statistics']['power_incidents']):
                    if incident['counter_changes']:
                        for change in incident['counter_changes']:
                            all_counter_changes.append({
                                'Incident #': i + 1,
                                'Incident Start': incident['start_time'].strftime('%Y-%m-%d %H:%M:%S') if incident['start_time'] else 'N/A',
                                'Timestamp': change['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if change['timestamp'] else 'N/A',
                                'Counter Value': change['counter_value'],
                                'Change': change['change'],
                                'Accumulated Production': change['counter_value'] - incident['start_counter']
                            })
                
                if all_counter_changes:
                    counter_changes_df = pd.DataFrame(all_counter_changes)
                    counter_changes_df.to_excel(writer, sheet_name='Counter Changes', index=False)
                
                # Counter changes by date sheet
                all_counter_changes_by_date = []
                for i, incident in enumerate(analysis['statistics']['power_incidents']):
                    if incident.get('counter_changes_by_date'):
                        for date_group in incident['counter_changes_by_date']:
                            all_counter_changes_by_date.append({
                                'Incident #': i + 1,
                                'Incident Start': incident['start_time'].strftime('%Y-%m-%d %H:%M:%S') if incident['start_time'] else 'N/A',
                                'Date': date_group['date_display'],
                                'Is Today': 'Yes' if date_group['is_today'] else 'No',
                                'Total Production': date_group['total'],
                                'Number of Changes': len(date_group['changes'])
                            })
                
                if all_counter_changes_by_date:
                    counter_changes_by_date_df = pd.DataFrame(all_counter_changes_by_date)
                    counter_changes_by_date_df.to_excel(writer, sheet_name='Counter Changes by Date', index=False)
                
                # Daily production without power sheet
                if analysis.get('daily_production_without_power'):
                    daily_production_data = []
                    for day in analysis['daily_production_without_power']:
                        daily_production_data.append({
                            'Date': day['date_display'],
                            'Is Today': 'Yes' if day['is_today'] else 'No',
                            'Has Power Outage': 'Yes' if day['has_power_outage'] else 'No',
                            'Start Counter': day['start_counter'] if day['start_counter'] else 'N/A',
                            'End Counter': day['end_counter'] if day['end_counter'] else 'N/A',
                            'Total Production Without Power': day['total_production_without_power']
                        })
                    
                    daily_production_df = pd.DataFrame(daily_production_data)
                    daily_production_df.to_excel(writer, sheet_name='Daily Production Without Power', index=False)
                
                # Power outages with production sheet
                if analysis.get('power_outages_with_production'):
                    power_outages_data = []
                    for outage in analysis['power_outages_with_production']:
                        power_outages_data.append({
                            'Type': 'Multiple' if outage['type'] == 'multiple' else 'Single',
                            'Date Range': outage['date_range'],
                            'Start Time': outage['start_time'].strftime('%Y-%m-%d %H:%M:%S') if outage['start_time'] else 'N/A',
                            'End Time': outage['end_time'].strftime('%Y-%m-%d %H:%M:%S') if outage['end_time'] else 'N/A',
                            'Duration (hours)': round(outage['duration'].total_seconds() / 3600, 2) if outage['duration'] else 0,
                            'Start Counter': outage['start_counter'],
                            'End Counter': outage['end_counter'] if outage['end_counter'] else 'N/A',
                            'Total Production': outage['total_production'],
                            'Is Ongoing': 'Yes' if outage['is_ongoing'] else 'No',
                            'Outage Count': outage.get('outage_count', 1)
                        })
                    
                    power_outages_df = pd.DataFrame(power_outages_data)
                    power_outages_df.to_excel(writer, sheet_name='Power Outages with Production', index=False)
                
                # Production events sheet
                all_production_events = []
                for i, outage in enumerate(analysis.get('power_outages_with_production', [])):
                    for event in outage.get('production_events', []):
                        all_production_events.append({
                            'Outage #': i + 1,
                            'Outage Type': 'Multiple' if outage['type'] == 'multiple' else 'Single',
                            'Date Range': outage['date_range'],
                            'Event Timestamp': event['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if event['timestamp'] else 'N/A',
                            'Time from Start': f"{event['time_from_start'].days}d {event['time_from_start'].seconds//3600}h {(event['time_from_start'].seconds%3600)//60}m" if event['time_from_start'] else 'N/A',
                            'Counter Value': event['counter_value'],
                            'Production Increment': event['production_increment'],
                            'Accumulated Production': event['counter_value'] - outage['start_counter']
                        })
                
                if all_production_events:
                    production_events_df = pd.DataFrame(all_production_events)
                    production_events_df.to_excel(writer, sheet_name='Production Events', index=False)
        
        output.seek(0)
        
        # Create response
        filename = f"power_analysis_{device.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('device_detailed_power_analysis', device_id=device_id)

@login_required
def export_incident_counter_changes(request, device_id):
    """Export specific incident counter changes to Excel - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. This page is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        from datetime import datetime
        
        device = get_object_or_404(Device, id=device_id)
        incident_start = request.GET.get('incident_start')
        
        if not incident_start:
            messages.error(request, 'Incident start time is required')
            return redirect('device_detailed_power_analysis', device_id=device_id)
        
        # Debug logging
        print(f"DEBUG: Export request for device {device.name}, incident_start: {incident_start}")
        
        power_service = UnifiedPowerManagementService()
        analysis = power_service.get_device_detailed_power_analysis(device)
        
        if not analysis['has_data']:
            messages.error(request, 'No data available for export')
            return redirect('device_detailed_power_analysis', device_id=device_id)
        
        # Find the specific incident
        target_incident = None
        print(f"DEBUG: Looking for incident with start time: {incident_start}")
        
        for i, incident in enumerate(analysis['statistics']['power_incidents']):
            print(f"DEBUG: Incident {i+1} start_time: {incident['start_time']}")
            if incident['start_time']:
                incident_str = incident['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"DEBUG: Comparing '{incident_str}' with '{incident_start}'")
                if incident_str == incident_start:
                    target_incident = incident
                    print(f"DEBUG: Found matching incident!")
                    break
        
        if not target_incident:
            messages.error(request, f'Incident not found for start time: {incident_start}')
            return redirect('device_detailed_power_analysis', device_id=device_id)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Incident summary
            summary_data = {
                'Metric': [
                    'Device Name',
                    'Incident Start',
                    'Incident End',
                    'Duration (hours)',
                    'Start Counter',
                    'End Counter',
                    'Total Production without Power',
                    'Has Counter Activity',
                    'Is Ongoing',
                    'Export Date'
                ],
                'Value': [
                    device.name,
                    target_incident['start_time'].strftime('%Y-%m-%d %H:%M:%S') if target_incident['start_time'] else 'N/A',
                    target_incident['end_time'].strftime('%Y-%m-%d %H:%M:%S') if target_incident['end_time'] else 'N/A',
                    round(target_incident['duration'].total_seconds() / 3600, 2) if 'duration' in target_incident else 0,
                    target_incident['start_counter'],
                    target_incident['end_counter'] if target_incident['end_counter'] else 'N/A',
                    target_incident['total_production'],
                    'Yes' if target_incident['has_counter_activity'] else 'No',
                    'Yes' if target_incident.get('is_ongoing', False) else 'No',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Incident Summary', index=False)
            
            # Counter changes
            if target_incident['counter_changes']:
                counter_changes_data = []
                for i, change in enumerate(target_incident['counter_changes']):
                    counter_changes_data.append({
                        'Sequence #': i + 1,
                        'Timestamp': change['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if change['timestamp'] else 'N/A',
                        'Counter Value': change['counter_value'],
                        'Change': change['change'],
                        'Accumulated Production': change['counter_value'] - target_incident['start_counter']
                    })
                
                counter_changes_df = pd.DataFrame(counter_changes_data)
                counter_changes_df.to_excel(writer, sheet_name='Counter Changes', index=False)
            
            # Counter changes by date
            if target_incident.get('counter_changes_by_date'):
                counter_changes_by_date_data = []
                for date_group in target_incident['counter_changes_by_date']:
                    counter_changes_by_date_data.append({
                        'Date': date_group['date_display'],
                        'Is Today': 'Yes' if date_group['is_today'] else 'No',
                        'Total Production': date_group['total'],
                        'Number of Changes': len(date_group['changes'])
                    })
                
                counter_changes_by_date_df = pd.DataFrame(counter_changes_by_date_data)
                counter_changes_by_date_df.to_excel(writer, sheet_name='Counter Changes by Date', index=False)
        
        output.seek(0)
        
        # Create response
        filename = f"incident_counter_changes_{device.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('device_detailed_power_analysis', device_id=device_id) 

@login_required
def export_power_outages(request, device_id):
    """Export power outages to Excel - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. This page is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        import pandas as pd
        from io import BytesIO
        from django.http import HttpResponse
        from datetime import datetime
        
        device = get_object_or_404(Device, id=device_id)
        power_service = UnifiedPowerManagementService()
        
        # Get detailed analysis
        analysis = power_service.get_device_detailed_power_analysis(device)
        
        if not analysis['has_data']:
            messages.error(request, 'No data available for export')
            return redirect('device_detailed_power_analysis', device_id=device_id)
        
        # Create Excel file
        output = BytesIO()
        
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                
                # Summary sheet
                summary_data = {
                    'Metric': [
                        'Device Name',
                        'Factory',
                        'Total Power Outages',
                        'Total Production without Power',
                        'Total Duration (hours)',
                        'Ongoing Outages',
                        'Export Date'
                    ],
                    'Value': [
                        device.name,
                        device.factory.name if device.factory else 'N/A',
                        len(analysis.get('power_outages_with_production', [])),
                        sum(outage['total_production'] for outage in analysis.get('power_outages_with_production', [])),
                        round(sum(outage['duration'].total_seconds() for outage in analysis.get('power_outages_with_production', [])) / 3600, 2),
                        sum(1 for outage in analysis.get('power_outages_with_production', []) if outage.get('is_ongoing', False)),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Power outages sheet
                if analysis.get('power_outages_with_production'):
                    outages_data = []
                    for i, outage in enumerate(analysis['power_outages_with_production']):
                        outages_data.append({
                            'Outage #': i + 1,
                            'Type': 'Multiple' if outage['type'] == 'multiple' else 'Single',
                            'Date Range': outage['date_range'],
                            'Time Range': outage['time_range'],
                            'Duration (hours)': round(outage['duration'].total_seconds() / 3600, 2) if outage['duration'] else 0,
                            'Start Counter': outage['start_counter'],
                            'End Counter': outage['end_counter'] if outage['end_counter'] else 'N/A',
                            'Total Production': outage['total_production'],
                            'Is Ongoing': 'Yes' if outage['is_ongoing'] else 'No',
                            'Outage Count': outage.get('outage_count', 1)
                        })
                    
                    outages_df = pd.DataFrame(outages_data)
                    outages_df.to_excel(writer, sheet_name='Power Outages', index=False)
                    
                    # Production events sheet
                    all_production_events = []
                    for i, outage in enumerate(analysis['power_outages_with_production']):
                        for event in outage.get('production_events', []):
                            all_production_events.append({
                                'Outage #': i + 1,
                                'Outage Type': 'Multiple' if outage['type'] == 'multiple' else 'Single',
                                'Date Range': outage['date_range'],
                                'Event Timestamp': event['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if event['timestamp'] else 'N/A',
                                'Time from Start': f"{event['time_from_start'].days}d {event['time_from_start'].seconds//3600}h {(event['time_from_start'].seconds%3600)//60}m" if event['time_from_start'] else 'N/A',
                                'Counter Value': event['counter_value'],
                                'Production Increment': event['production_increment'],
                                'Cumulative': event.get('cumulative', event['production_increment'])
                            })
                    
                    if all_production_events:
                        production_events_df = pd.DataFrame(all_production_events)
                        production_events_df.to_excel(writer, sheet_name='Production Events', index=False)
            
            output.seek(0)
            
            # Create response
            filename = f"power_outages_{device.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as excel_error:
            print(f"Excel creation error: {str(excel_error)}")
            messages.error(request, f'Error creating Excel file: {str(excel_error)}')
            return redirect('device_detailed_power_analysis', device_id=device_id)
        
    except Exception as e:
        print(f"Export error: {str(e)}")
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('device_detailed_power_analysis', device_id=device_id)
 

@login_required
def device_power_history(request, device_id):
    """Show device power history with date range filtering - Super admin only"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. This page is only available for super administrators.')
        return redirect('dashboard')
    
    try:
        device = get_object_or_404(Device, id=device_id)
        power_service = UnifiedPowerManagementService()
        
        # Get date range from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        days = request.GET.get('days', '30')
        
        # Convert days to integer
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        # Get date range for power history
        if start_date and end_date:
            # Use specific date range
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            days = (end_dt - start_dt).days + 1
        
        # Get detailed analysis with specified days
        analysis = power_service.get_device_detailed_power_analysis(device, days=days)
        
        context = {
            'device': device,
            'analysis': analysis,
            'selected_days': days,
            'start_date': start_date,
            'end_date': end_date,
        }
        
        return render(request, 'mill/device_power_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading device history: {str(e)}')
        return redirect('device_detailed_power_analysis', device_id=device_id) 