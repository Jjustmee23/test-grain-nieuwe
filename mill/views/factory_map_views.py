from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from mill.models import Factory, ProductionData, Device
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta


@login_required
def factory_map(request):
    """Display a map with all factories and their locations"""
    
    # Get all factories with coordinates
    factories = Factory.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('city')
    
    # Get daily production data for each factory
    today = timezone.now().date()
    factory_data = []
    
    for factory in factories:
        # Get all devices for this factory
        devices = factory.devices.all()
        
        # Calculate total daily production for all devices
        total_daily = 0
        active_devices = 0
        
        for device in devices:
            try:
                # Get the latest production data for this device
                latest_data = ProductionData.objects.filter(
                    device=device,
                    created_at__date=today
                ).order_by('-created_at').first()
                
                if latest_data:
                    total_daily += latest_data.daily_production
                    active_devices += 1
            except:
                continue
        
        factory_data.append({
            'id': factory.id,
            'name': factory.name,
            'city': factory.city.name if factory.city else 'Unknown',
            'address': factory.address or 'No address provided',
            'latitude': float(factory.latitude),
            'longitude': float(factory.longitude),
            'status': factory.status,
            'daily_production': total_daily,
            'active_devices': active_devices,
            'total_devices': devices.count(),
        })
    
    context = {
        'factories': factory_data,
        'total_factories': len(factory_data),
        'active_factories': len([f for f in factory_data if f['status']]),
    }
    
    return render(request, 'mill/factory_map.html', context)


@login_required
def factory_map_data(request):
    """API endpoint to get factory data for the map"""
    
    # Get all factories with coordinates
    factories = Factory.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('city')
    
    # Get daily production data
    today = timezone.now().date()
    factory_data = []
    
    for factory in factories:
        devices = factory.devices.all()
        total_daily = 0
        active_devices = 0
        
        for device in devices:
            try:
                latest_data = ProductionData.objects.filter(
                    device=device,
                    created_at__date=today
                ).order_by('-created_at').first()
                
                if latest_data:
                    total_daily += latest_data.daily_production
                    active_devices += 1
            except:
                continue
        
        factory_data.append({
            'id': factory.id,
            'name': factory.name,
            'city': factory.city.name if factory.city else 'Unknown',
            'address': factory.address or 'No address provided',
            'latitude': float(factory.latitude),
            'longitude': float(factory.longitude),
            'status': factory.status,
            'daily_production': total_daily,
            'active_devices': active_devices,
            'total_devices': devices.count(),
            'status_color': 'green' if factory.status else 'red',
        })
    
    return JsonResponse({
        'factories': factory_data,
        'total_factories': len(factory_data),
        'active_factories': len([f for f in factory_data if f['status']]),
    }) 