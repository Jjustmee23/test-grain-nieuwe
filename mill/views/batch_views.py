from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import transaction
from mill.models import Batch, Factory, FlourBagCount, BatchNotification, RawData, ProductionData
from mill.forms import BatchForm
from mill.utils import is_super_admin , allowed_factories
from datetime import datetime
import logging
from decimal import Decimal
from django.db.models.functions import TruncDate
from django.db.models import Sum, Max, Min
import datetime

class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = 'batches/batch_list.html'
    context_object_name = 'batches'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        allowed_factories_list = allowed_factories(self.request)
        queryset = queryset.filter(factory__in=allowed_factories_list)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print('context data')
        # context['factories'] = [Factory.objects.filter(status=True)]
        context['is_super_admin'] = is_super_admin(self.request.user)
        return context

class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'batches/batch_form.html'
    success_url = reverse_lazy('batch-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure cities are available in the template
        from mill.models import City
        context['cities'] = City.objects.filter(status=True).order_by('name')
        return context

    def form_valid(self, form):
        # Get the selected cities and factories
        cities = form.cleaned_data.get('cities')
        factories = form.cleaned_data.get('factories')
        
        if not cities or not factories:
            form.add_error(None, 'Please select at least one city and one factory.')
            return self.form_invalid(form)
        
        # Validate that factories belong to selected cities
        selected_city_ids = set(cities.values_list('id', flat=True))
        for factory in factories:
            if factory.city_id not in selected_city_ids:
                form.add_error('factories', f'Factory "{factory.name}" does not belong to any selected city.')
                return self.form_invalid(form)
        
        # Create a batch for each selected factory
        created_batches = []
        base_batch_number = form.cleaned_data.get('batch_number')
        wheat_amount = form.cleaned_data.get('wheat_amount')
        waste_factor = form.cleaned_data.get('waste_factor')
        
        for i, factory in enumerate(factories):
            # Create unique batch number for each factory
            if len(factories) > 1:
                batch_number = f"{base_batch_number}-{factory.name}-{i+1}"
            else:
                batch_number = base_batch_number
            
            # Check if batch number already exists
            if Batch.objects.filter(batch_number=batch_number).exists():
                form.add_error('batch_number', f'Batch number "{batch_number}" already exists.')
                return self.form_invalid(form)
            
            # Create the batch
            batch = Batch.objects.create(
                batch_number=batch_number,
                factory=factory,
                wheat_amount=wheat_amount,
                waste_factor=waste_factor,
                created_by=self.request.user
            )
            
            # Try to set start_value and current_value from device data
            try:
                device = factory.devices.first()
                if device:
                    current_value = self.get_current_device_counter(device)
                    batch.start_value = current_value
                    batch.current_value = 0
                    batch.save()
                else:
                    messages.warning(self.request, f'No device found for factory {factory.name}')
            except Exception as e:
                messages.warning(self.request, f'Error calculating counter values for {factory.name}: {str(e)}')
            
            created_batches.append(batch)
        
        # Show success message
        if len(created_batches) == 1:
            messages.success(self.request, f'Batch "{created_batches[0].batch_number}" created successfully!')
        else:
            batch_numbers = [b.batch_number for b in created_batches]
            messages.success(self.request, f'Created {len(created_batches)} batches: {", ".join(batch_numbers)}')
        
        return super().form_valid(form)
    
    def get_current_device_counter(self, device):
        """Get current device counter value from ProductionData"""
        try:
            # Get the latest reading from ProductionData using updated_at
            reading = ProductionData.objects.filter(device=device).order_by('-updated_at').first()
            
            if reading:
                # Use daily_production as the counter value
                return reading.daily_production
            else:
                return 0
        except Exception:
            return 0

class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'batches/batch_detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.get_object()
        context['flour_bag_counts'] = batch.flour_bag_counts.all().order_by('-timestamp')
        context['alerts'] = batch.alerts.all().order_by('-created_at')
        
        # --- ProductionData batch-specific calculation ---
        from django.db.models.functions import TruncDate
        from django.db.models import Max, Min
        import datetime
        
        today = datetime.date.today()
        
        # Get the device for this batch's factory
        device = batch.factory.devices.first()
        
        if device:
            # Filter ProductionData from batch start date onwards
            batch_start_date = batch.start_date.date()
            CONVERSION_FACTOR = 50  # kg per unit
            
            # Get ProductionData for this device, filtered by batch start date, grouped by date
            daily_production_data = (
                ProductionData.objects
                .filter(
                    device=device,
                    created_at__date__gte=batch_start_date  # From batch start date onwards
                )
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .order_by('day')
            )
            
            # Calculate daily differences (end - start for each day) from batch start
            daily_values = []
            cumulative_units = 0
            
            for entry in daily_production_data:
                day = entry['day']
                
                # Get start and end values for this day
                day_start = ProductionData.objects.filter(
                    device=device,
                    created_at__date=day
                ).aggregate(start_value=Min('daily_production'))['start_value'] or 0
                
                day_end = ProductionData.objects.filter(
                    device=device,
                    created_at__date=day
                ).aggregate(end_value=Max('daily_production'))['end_value'] or 0
                
                # Calculate difference (daily production)
                daily_production = day_end - day_start
                cumulative_units += daily_production
                
                # Convert to tons for this cumulative value
                cumulative_tons_for_day = (cumulative_units * CONVERSION_FACTOR) / 1000
                
                daily_values.append({
                    'day': day,
                    'production': daily_production,
                    'start_value': day_start,
                    'end_value': day_end,
                    'cumulative': cumulative_units,
                    'cumulative_tons': cumulative_tons_for_day
                })
            
            # Today's value (last day in the data)
            today_value = daily_values[-1]['production'] if daily_values else 0
            
            # Calculate remaining production
            expected_tons = float(batch.expected_flour_output)
            final_cumulative_tons = (cumulative_units * CONVERSION_FACTOR) / 1000
            remaining_tons = max(0, expected_tons - final_cumulative_tons)
            
            # Batch progress percentage
            progress_percentage = (final_cumulative_tons / expected_tons * 100) if expected_tons > 0 else 0
            
            context['daily_production_values'] = daily_values
            context['today_production'] = today_value
            context['cumulative_units'] = cumulative_units
            context['cumulative_kg'] = cumulative_units * CONVERSION_FACTOR
            context['cumulative_tons'] = final_cumulative_tons
            context['remaining_tons'] = remaining_tons
            context['progress_percentage'] = progress_percentage
            context['conversion_factor'] = CONVERSION_FACTOR
            context['batch_start_date'] = batch_start_date
        else:
            context['daily_production_values'] = []
            context['today_production'] = 0
            context['cumulative_units'] = 0
            context['cumulative_kg'] = 0
            context['cumulative_tons'] = 0
            context['remaining_tons'] = float(batch.expected_flour_output)
            context['progress_percentage'] = 0
            context['conversion_factor'] = 50
            context['batch_start_date'] = batch.start_date.date()
        
        return context
logger = logging.getLogger(__name__)

class BatchUpdateView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk):
        try:
            batch = Batch.objects.select_for_update().get(pk=pk)
            
            # Check if batch can be edited
            if not batch.can_be_edited:
                return JsonResponse({
                    'success': False,
                    'error': f'Batch cannot be edited in {batch.get_status_display()} status'
                }, status=400)
            
            # Get form data with default values
            wheat_amount = request.POST.get('wheat_amount')
            waste_factor = request.POST.get('waste_factor')
            actual_flour_output = request.POST.get('actual_flour_output')
            is_completed = request.POST.get('is_completed') == 'true'
            
            # Convert and validate data
            try:
                if wheat_amount:
                    wheat_amount = float(wheat_amount)
                    if wheat_amount <= 0:
                        return JsonResponse({
                            'success': False, 
                            'error': 'Wheat amount must be greater than 0'
                        })
                    batch.wheat_amount = wheat_amount

                if waste_factor:
                    waste_factor = float(waste_factor)
                    if not (0 <= waste_factor <= 100):
                        return JsonResponse({
                            'success': False, 
                            'error': 'Waste factor must be between 0 and 100'
                        })
                    batch.waste_factor = waste_factor

                if actual_flour_output:
                    actual_flour_output = float(actual_flour_output)
                    if actual_flour_output < 0:
                        return JsonResponse({
                            'success': False, 
                            'error': 'Actual output cannot be negative'
                        })
                    batch.actual_flour_output = actual_flour_output

            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid numeric values provided'
                })

            # Update expected output if wheat amount or waste factor changed
            if wheat_amount or waste_factor:
                batch.expected_flour_output = Decimal(str(batch.wheat_amount)) * (Decimal('100') - Decimal(str(batch.waste_factor))) / Decimal('100')

            # Handle batch completion
            if is_completed and not batch.is_completed:
                batch.is_completed = True
                batch.end_date = timezone.now()
            
            # Record who made the changes
            batch.save()
            
            # Handle production entry if provided
            bag_count = request.POST.get('bag_count')
            bags_weight = request.POST.get('bags_weight')
            
            if bag_count and bags_weight:
                try:
                    bag_count = int(bag_count)
                    bags_weight = float(bags_weight)
                    
                    if bag_count < 0 or bags_weight < 0:
                        return JsonResponse({
                            'success': False,
                            'error': 'Bag count and weight must be positive numbers'
                        })
                        
                    # Get the first device from the factory for this batch
                    device = batch.factory.devices.first()
                    if device:
                        FlourBagCount.objects.create(
                            batch=batch,
                            bag_count=bag_count,
                            device=device,
                            bags_weight=bags_weight,
                            timestamp=timezone.now(),
                            created_by=request.user 
                        )
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'No device found for this factory'
                        })
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid bag count or weight values'
                    })
            
            return JsonResponse({
                'success': True,
                'message': 'Batch updated successfully',
                'data': {
                    'wheat_amount': batch.wheat_amount,
                    'waste_factor': batch.waste_factor,
                    'actual_flour_output': batch.actual_flour_output,
                    'expected_flour_output': batch.expected_flour_output,
                    'is_completed': batch.is_completed,
                    'updated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
        except Batch.DoesNotExist:
            logger.error(f"Batch {pk} not found")
            return JsonResponse({
                'success': False, 
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error updating batch {pk}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'An error occurred while updating the batch: {str(e)}'
            }, status=500)

class BatchManagementView(LoginRequiredMixin, View):
    """View for batch management actions (approve, start, pause, stop) - Super Admin only"""
    
    def post(self, request, pk):
        if not is_super_admin(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Only Super Admins can perform batch management actions'
            }, status=403)
        
        try:
            batch = Batch.objects.get(pk=pk)
            action = request.POST.get('action')
            
            if action == 'approve':
                batch.status = 'approved'
                batch.approved_by = request.user
                batch.approved_at = timezone.now()
                messages.success(request, f'Batch {batch.batch_number} approved successfully!')
                
            elif action == 'start':
                batch.status = 'in_process'
                messages.success(request, f'Batch {batch.batch_number} started successfully!')
                
            elif action == 'pause':
                batch.status = 'paused'
                messages.success(request, f'Batch {batch.batch_number} paused successfully!')
                
            elif action == 'stop':
                # Finalize the batch - set to stopped and lock all values
                batch.finalize_batch(request.user)
                messages.success(request, f'Batch {batch.batch_number} stopped and finalized!')
                
            elif action == 'finalize':
                # Alternative way to finalize a batch
                batch.finalize_batch(request.user)
                messages.success(request, f'Batch {batch.batch_number} finalized!')
                
            elif action == 'reject':
                batch.status = 'rejected'
                messages.success(request, f'Batch {batch.batch_number} rejected!')
                
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action specified'
                }, status=400)
            
            batch.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Batch {batch.batch_number} {action}ed successfully',
                'data': {
                    'status': batch.status,
                    'status_display': batch.get_status_display(),
                    'is_completed': batch.is_completed
                }
            })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error in batch management: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }, status=500)

class BatchCounterUpdateView(LoginRequiredMixin, View):
    """View for updating batch counter values - Super Admin only, manual correction only"""
    
    def post(self, request, pk):
        if not is_super_admin(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Only Super Admins can update counter values'
            }, status=403)
        
        try:
            batch = Batch.objects.get(pk=pk)
            
            # Check if batch can be updated (not finalized)
            if batch.is_finalized:
                return JsonResponse({
                    'success': False,
                    'error': f'Batch cannot be updated in {batch.get_status_display()} status'
                }, status=400)
            
            # Check if batch is approved or in process
            if batch.status not in ['approved', 'in_process']:
                return JsonResponse({
                    'success': False,
                    'error': 'Batch must be approved or in process before updating counter values'
                }, status=400)
            
            # Get manual correction value from POST
            correction = request.POST.get('correction')
            try:
                correction = int(correction)
            except (TypeError, ValueError):
                return JsonResponse({
                    'success': False,
                    'error': 'Correction value must be an integer'
                }, status=400)
            
            # Apply correction (can be positive or negative)
            batch.current_value += correction
            if batch.current_value < 0:
                batch.current_value = 0
            
            # Update flour output
            batch.actual_flour_output = Decimal(str(batch.current_value)) * Decimal('0.05')
            batch.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Counter manually updated by {correction} units.',
                'data': {
                    'current_value': batch.current_value,
                    'actual_flour_output': float(batch.actual_flour_output),
                    'progress_percentage': batch.progress_percentage,
                }
            })
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error updating counter: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }, status=500)

class BatchNotificationView(LoginRequiredMixin, View):
    """View for batch notifications"""
    
    def get(self, request):
        user_notifications = BatchNotification.objects.filter(
            sent_to=request.user
        ).order_by('-sent_at')[:10]
        
        return JsonResponse({
            'success': True,
            'notifications': [
                {
                    'id': notif.id,
                    'type': notif.notification_type,
                    'message': notif.message,
                    'sent_at': notif.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_read': notif.is_read,
                    'batch_number': notif.batch.batch_number,
                    'factory_name': notif.batch.factory.name
                }
                for notif in user_notifications
            ]
        })
    
    def post(self, request):
        """Mark notification as read"""
        notification_id = request.POST.get('notification_id')
        
        try:
            notification = BatchNotification.objects.get(
                id=notification_id,
                sent_to=request.user
            )
            notification.is_read = True
            notification.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })
            
        except BatchNotification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Notification not found'
            }, status=404)

class BatchAutoUpdateView(LoginRequiredMixin, View):
    """View for automatically updating batch current values from device data"""
    
    def post(self, request, pk):
        if not is_super_admin(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Only Super Admins can auto-update batches'
            }, status=403)
        
        try:
            batch = Batch.objects.get(pk=pk)
            
            # Check if batch can be updated (not finalized)
            if batch.is_finalized:
                return JsonResponse({
                    'success': False,
                    'error': f'Batch cannot be updated in {batch.get_status_display()} status'
                }, status=400)
            
            # Get device for this batch
            device = batch.factory.devices.first()
            if not device:
                return JsonResponse({
                    'success': False,
                    'error': 'No device found for this factory'
                }, status=400)
            
            # Get current device counter from TransactionData (daily production)
            from mill.models import TransactionData
            current_reading = TransactionData.objects.filter(device=device).order_by('-created_at').first()
            
            if not current_reading:
                return JsonResponse({
                    'success': False,
                    'error': 'No device data available for this factory. Batch will remain unchanged.'
                }, status=400)
            
            # Use daily_production as the current counter value
            current_device_value = current_reading.daily_production
            
            # Calculate new current_value based on device counter difference
            # current_value = device_counter_now - device_counter_at_start
            new_current_value = current_device_value - batch.start_value
            
            if new_current_value < 0:
                new_current_value = 0
            
            # Update batch
            old_current_value = batch.current_value
            batch.current_value = new_current_value
            batch.actual_flour_output = Decimal(str(batch.current_value)) * Decimal('0.05')  # 1 unit = 50kg = 0.05 tons
            batch.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Batch updated successfully! Old value: {old_current_value}, New value: {new_current_value}',
                'data': {
                    'current_value': batch.current_value,
                    'actual_flour_output': float(batch.actual_flour_output),
                    'progress_percentage': batch.progress_percentage,
                    'device_counter': current_device_value,
                    'start_value': batch.start_value
                }
            })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error updating batch: {str(e)}'
            }, status=500)