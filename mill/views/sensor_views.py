from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from mill.models import Device, FlourBagCount, Batch, Alert, RawData
from mill.services.power_management_service import PowerManagementService
import json

@csrf_exempt
@require_http_methods(["POST"])
def sensor_data_receiver(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        bag_count = data.get('bag_count')
        bags_weight = data.get('bags_weight')
        batch_number = data.get('batch_number')

        device = Device.objects.get(id=device_id)
        batch = Batch.objects.get(batch_number=batch_number, is_completed=False)

        # Create flour bag count entry
        flour_count = FlourBagCount.objects.create(
            batch=batch,
            device=device,
            bag_count=bag_count,
            bags_weight=bags_weight
        )

        # Update batch actual output
        batch.actual_flour_output = bags_weight
        batch.save()

        # Check for significant deviation
        expected_output = batch.expected_flour_output
        if bags_weight < (expected_output * 0.9):  # Less than 90% of expected
            Alert.objects.create(
                batch=batch,
                alert_type='PRODUCTION_LOW',
                severity='HIGH',
                message=f'Production is below 90% of target. Expected: {expected_output} tons, Actual: {bags_weight} tons'
            )

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def sensor_status(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    return JsonResponse({
        'status': device.status,
        'last_reading': device.flour_bag_counts.last().timestamp if device.flour_bag_counts.exists() else None
    })

@csrf_exempt
@require_http_methods(["POST"])
def mqtt_data_receiver(request):
    """Receive MQTT data from devices and process power management"""
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        
        # Get or create device
        device, created = Device.objects.get_or_create(
            id=device_id,
            defaults={'name': f'Device {device_id}', 'status': True}
        )
        
        # Create RawData entry
        raw_data = RawData.objects.create(
            device=device,
            timestamp=data.get('timestamp'),
            mobile_signal=data.get('mobile_signal'),
            dout_enabled=data.get('dout_enabled'),
            dout=data.get('dout'),
            di_mode=data.get('di_mode'),
            din=data.get('din'),
            counter_1=data.get('counter_1'),
            counter_2=data.get('counter_2'),
            counter_3=data.get('counter_3'),
            counter_4=data.get('counter_4'),
            ain_mode=data.get('ain_mode'),
            ain1_value=data.get('ain1_value'),  # Power value
            ain2_value=data.get('ain2_value'),
            ain3_value=data.get('ain3_value'),
            ain4_value=data.get('ain4_value'),
            ain5_value=data.get('ain5_value'),
            ain6_value=data.get('ain6_value'),
            ain7_value=data.get('ain7_value'),
            ain8_value=data.get('ain8_value'),
            start_flag=data.get('start_flag'),
            type=data.get('type'),
            length=data.get('length'),
            version=data.get('version'),
            end_flag=data.get('end_flag')
        )
        
        # Process power management
        power_service = PowerManagementService()
        power_service.process_raw_data(raw_data)
        
        return JsonResponse({'status': 'success', 'message': 'MQTT data processed'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)