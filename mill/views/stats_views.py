from django.shortcuts import render, get_object_or_404, redirect
from mill.models import Factory, ProductionData, Device, UserProfile, Batch, FlourBagCount
from django.contrib import messages
from datetime import date, datetime
from django.db.models import Sum
from django.db.models.functions import TruncHour
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from mill.utils import calculate_chart_data, is_allowed_factory

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

        # Get batches for this factory
        batches = Batch.objects.filter(
            factory=factory
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
                'start_date': batch.start_date,
                'status': batch.get_status_display(),
                'is_completed': batch.is_completed,
                'wheat_amount': float(batch.wheat_amount or 0),
                'expected_flour_output': float(batch.expected_flour_output or 0),
                'actual_flour_output': float(batch.actual_flour_output or 0),
                'waste_factor': float(batch.waste_factor or 0),
                'yield_rate': yield_rate,
                'detail_url': reverse('batch-detail', kwargs={'pk': batch.id})  # Add URL for detail view
            }
            batch_details.append(batch_detail)

        context = {
            'factory': factory,
            'selected_date': timezone.now().date(),
            'current_year': datetime.now().year,
            'batches': batch_details,
            'total_batches': len(batch_details)
        }

        return render(request, 'mill/view_statistics.html', context)
    
   
@login_required
def batch_detail(request, pk):
    
        batch = get_object_or_404(Batch.objects.select_related('factory')
                                 .prefetch_related('flour_bag_counts', 'alerts'), pk=pk)
        
        # Calculate yield rate
        yield_rate = (batch.actual_flour_output / batch.expected_flour_output * 100) if batch.expected_flour_output else 0
        
        # Get hourly production data
        hourly_data = batch.flour_bag_counts.annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            total_bags=Sum('bag_count'),
            total_weight=Sum('bags_weight')
        ).order_by('hour')

        context = {
            'batch': batch,
            'yield_rate': yield_rate,
            'hourly_data': hourly_data,
            'alerts': batch.alerts.all()
        }
        
        return render(request, 'batches/batch_detail.html', context)
    
 