from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connections
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@login_required
def test_page(request):
    """
    MQTT Monitor - Read-only system for monitoring devices
    - testdb.mill_device: Device names (read-only)
    - counter.mqtt_data: MQTT data (read-only)
    - Updates every 5 minutes
    """
    try:
        # Get all devices from mill_device table (READ-ONLY)
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT id, name, status FROM mill_device ORDER BY id")
            mill_devices = {row[0]: {'name': row[1], 'status': row[2]} for row in cursor.fetchall()}
        
        # Get all unique device IDs from counter.mqtt_data (READ-ONLY)
        with connections['counter'].cursor() as cursor:
            cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id")
            active_device_ids = [row[0] for row in cursor.fetchall()]
        
        # Combine all devices (active + mill_device devices)
        all_device_ids = list(set(list(mill_devices.keys()) + active_device_ids))
        all_device_ids.sort()
        
        # Get latest data for each device (READ-ONLY)
        device_data = []
        for device_id in all_device_ids:
            # Get latest record for this device from counter.mqtt_data (READ-ONLY)
            with connections['counter'].cursor() as cursor:
                cursor.execute("""
                    SELECT counter_id, timestamp, mobile_signal, din,
                           counter_1, counter_2, counter_3, counter_4,
                           ain1_value, ain2_value, ain3_value, ain4_value
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, [device_id])
                
                latest_record = cursor.fetchone()
            
            # Get device info from mill_device (READ-ONLY)
            device_info = mill_devices.get(device_id, {'name': None, 'status': False})
            device_name = device_info['name']
            device_status = device_info['status']
            
            if latest_record:
                # Check if device is truly active (data in last 10 minutes)
                timestamp = timezone.make_aware(latest_record[1]) if latest_record[1] else None
                ten_minutes_ago = timezone.now() - timedelta(minutes=10)
                
                if timestamp and timestamp >= ten_minutes_ago:
                    device_status_online = 'active'
                else:
                    device_status_online = 'offline'
                
                device_data_info = {
                    'device_id': latest_record[0],
                    'device_name': device_name,
                    'device_status': device_status,
                    'timestamp': timestamp,
                    'mobile_signal': latest_record[2],
                    'din': latest_record[3],
                    'counter_1': latest_record[4],
                    'counter_2': latest_record[5],
                    'counter_3': latest_record[6],
                    'counter_4': latest_record[7],
                    'ain1_value': latest_record[8],
                    'ain2_value': latest_record[9],
                    'ain3_value': latest_record[10],
                    'ain4_value': latest_record[11],
                    'time_since_update': timestamp,
                    'status': device_status_online,
                    'has_name': device_name is not None,
                    'is_enabled': device_status,
                }
            else:
                # Device is offline (no recent data)
                device_data_info = {
                    'device_id': device_id,
                    'device_name': device_name,
                    'device_status': device_status,
                    'timestamp': None,
                    'mobile_signal': None,
                    'din': None,
                    'counter_1': None,
                    'counter_2': None,
                    'counter_3': None,
                    'counter_4': None,
                    'ain1_value': None,
                    'ain2_value': None,
                    'ain3_value': None,
                    'ain4_value': None,
                    'time_since_update': None,
                    'status': 'offline',
                    'has_name': device_name is not None,
                    'is_enabled': device_status,
                }
            
            device_data.append(device_data_info)
        
        # Sort by status (active first) then by device_id
        device_data.sort(key=lambda x: (x['status'] != 'active', x['device_id']))
        
        # Get overall statistics (READ-ONLY)
        total_devices = len(device_data)
        active_devices = len([d for d in device_data if d['status'] == 'active'])
        offline_devices = len([d for d in device_data if d['status'] == 'offline'])
        named_devices = len([d for d in device_data if d['has_name']])
        unnamed_devices = total_devices - named_devices
        enabled_devices = len([d for d in device_data if d['is_enabled']])
        disabled_devices = total_devices - enabled_devices
        
        # Get total data count from counter.mqtt_data (READ-ONLY)
        with connections['counter'].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mqtt_data")
            total_data_count = cursor.fetchone()[0]
            
            # Get data from last 5 minutes (using UTC)
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            cursor.execute("""
                SELECT COUNT(*) FROM mqtt_data 
                WHERE timestamp >= %s
            """, [five_minutes_ago])
            recent_data_count = cursor.fetchone()[0]
            
            # Get active devices (with data in last 10 minutes - devices are online if they sent data in last 10 min)
            ten_minutes_ago = timezone.now() - timedelta(minutes=10)
            cursor.execute("""
                SELECT COUNT(DISTINCT counter_id) FROM mqtt_data 
                WHERE timestamp >= %s
            """, [ten_minutes_ago])
            truly_active_devices = cursor.fetchone()[0]
        
        context = {
            'device_data': device_data,
            'total_devices': total_devices,
            'active_devices': active_devices,
            'offline_devices': offline_devices,
            'named_devices': named_devices,
            'unnamed_devices': unnamed_devices,
            'enabled_devices': enabled_devices,
            'disabled_devices': disabled_devices,
            'total_data_count': total_data_count,
            'recent_data_count': recent_data_count,
            'truly_active_devices': truly_active_devices,
            'current_time': timezone.now(),
            'last_update': timezone.now(),
        }
        
        return render(request, 'mill/test_page.html', context) 
        
    except Exception as e:
        logger.error(f"Error in test_page: {e}")
        context = {
            'error': str(e),
            'device_data': [],
            'total_devices': 0,
            'active_devices': 0,
            'offline_devices': 0,
            'named_devices': 0,
            'unnamed_devices': 0,
            'enabled_devices': 0,
            'disabled_devices': 0,
            'total_data_count': 0,
            'recent_data_count': 0,
            'truly_active_devices': 0,
            'current_time': timezone.now(),
        }
        return render(request, 'mill/test_page.html', context) 


@login_required
def ajax_update(request):
    """
    AJAX endpoint for real-time device data updates
    """
    try:
        # Get all devices from mill_device table (READ-ONLY)
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT id, name, status FROM mill_device ORDER BY id")
            mill_devices = {row[0]: {'name': row[1], 'status': row[2]} for row in cursor.fetchall()}
        
        # Get all unique device IDs from counter.mqtt_data (READ-ONLY)
        with connections['counter'].cursor() as cursor:
            cursor.execute("SELECT DISTINCT counter_id FROM mqtt_data ORDER BY counter_id")
            active_device_ids = [row[0] for row in cursor.fetchall()]
        
        # Combine all devices
        all_device_ids = list(set(list(mill_devices.keys()) + active_device_ids))
        all_device_ids.sort()
        
        # Get latest data for each device
        devices_data = []
        for device_id in all_device_ids:
            with connections['counter'].cursor() as cursor:
                cursor.execute("""
                    SELECT counter_id, timestamp, mobile_signal, din,
                           counter_1, counter_2, counter_3, counter_4,
                           ain1_value, ain2_value, ain3_value, ain4_value
                    FROM mqtt_data 
                    WHERE counter_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, [device_id])
                
                latest_record = cursor.fetchone()
            
            device_info = mill_devices.get(device_id, {'name': None, 'status': False})
            
            if latest_record:
                # Calculate time since update and check if device is online
                timestamp = timezone.make_aware(latest_record[1]) if latest_record[1] else None
                ten_minutes_ago = timezone.now() - timedelta(minutes=10)
                
                # Determine if device is online (data in last 10 minutes)
                if timestamp and timestamp >= ten_minutes_ago:
                    device_status_online = 'active'
                else:
                    device_status_online = 'offline'
                
                time_since_update = None
                if timestamp:
                    time_diff = timezone.now() - timestamp
                    if time_diff.days > 0:
                        time_since_update = f"{time_diff.days} day{'s' if time_diff.days != 1 else ''}"
                    elif time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        time_since_update = f"{hours} hour{'s' if hours != 1 else ''}"
                    elif time_diff.seconds > 60:
                        minutes = time_diff.seconds // 60
                        time_since_update = f"{minutes} minute{'s' if minutes != 1 else ''}"
                    else:
                        time_since_update = f"{time_diff.seconds} second{'s' if time_diff.seconds != 1 else ''}"
                
                devices_data.append({
                    'device_id': latest_record[0],
                    'timestamp': timestamp.strftime('%b %d, %H:%M:%S') if timestamp else None,
                    'time_since_update': time_since_update,
                    'ain1_value': latest_record[8],
                    'counter_1': latest_record[4],
                    'status': device_status_online
                })
        
        # Get statistics
        with connections['counter'].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM mqtt_data")
            total_data_count = cursor.fetchone()[0]
            
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            cursor.execute("""
                SELECT COUNT(*) FROM mqtt_data 
                WHERE timestamp >= %s
            """, [five_minutes_ago])
            recent_data_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT counter_id) FROM mqtt_data 
                WHERE timestamp >= %s
            """, [five_minutes_ago])
            truly_active_devices = cursor.fetchone()[0]
        
        statistics = {
            'truly_active_devices': truly_active_devices,
            'offline_devices': len(all_device_ids) - truly_active_devices,
            'recent_data_count': recent_data_count,
            'total_data_count': total_data_count
        }
        
        return JsonResponse({
            'success': True,
            'devices': devices_data,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Error in ajax_update: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 