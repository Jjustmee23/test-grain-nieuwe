from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from mill.models import Device, FlourBagCount, Batch, Alert
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