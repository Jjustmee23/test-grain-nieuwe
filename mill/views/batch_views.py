from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import transaction
from mill.models import Batch, Factory, FlourBagCount, BatchNotification, RawData, ProductionData, BatchTemplate
from mill.forms import BatchForm
from mill.utils import is_super_admin, allowed_factories
from mill.services.batch_production_service import BatchProductionService
from mill.services.batch_notification_service import BatchNotificationService
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
        
        # Optimize database queries with select_related
        queryset = queryset.select_related('factory', 'factory__city', 'approved_by')
        
        # Add filtering
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        factory_filter = self.request.GET.get('factory')
        if factory_filter:
            queryset = queryset.filter(factory_id=factory_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_super_admin'] = is_super_admin(self.request.user)
        context['factories'] = Factory.objects.filter(status=True).order_by('name')
        context['status_choices'] = Batch.STATUS_CHOICES
        
        # Add batch templates
        context['batch_templates'] = BatchTemplate.objects.filter(is_active=True)
        
        # Add summary statistics
        service = BatchProductionService()
        context['summary_stats'] = self._get_summary_stats()
        
        # Add individual stats to context for template
        stats = self._get_summary_stats()
        context['total_batches'] = stats['total_batches']
        context['pending_batches'] = self.get_queryset().filter(status='pending').count()
        context['in_process_batches'] = stats['active_batches']
        context['completed_batches'] = stats['completed_batches']
        
        return context
    
    def _get_summary_stats(self):
        """Get summary statistics for batches"""
        queryset = self.get_queryset()
        
        stats = {
            'total_batches': queryset.count(),
            'active_batches': queryset.filter(status__in=['approved', 'in_process', 'paused']).count(),
            'completed_batches': queryset.filter(status='completed').count(),
            'total_expected_output': float(queryset.aggregate(Sum('expected_flour_output'))['expected_flour_output__sum'] or 0),
            'total_actual_output': float(queryset.aggregate(Sum('actual_flour_output'))['actual_flour_output__sum'] or 0),
        }
        
        if stats['total_expected_output'] > 0:
            stats['overall_progress'] = (stats['total_actual_output'] / stats['total_expected_output']) * 100
        else:
            stats['overall_progress'] = 0
        
        return stats

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
        context['batch_templates'] = BatchTemplate.objects.filter(is_active=True)
        return context
    
    def get_success_url(self):
        """Override to handle case where self.object might be None"""
        if hasattr(self, 'object') and self.object is not None:
            return super().get_success_url()
        else:
            # Fallback to hardcoded success URL
            return reverse_lazy('batch-list')

    def form_valid(self, form):
        # Get the selected cities and factories
        cities = form.cleaned_data.get('cities')
        factories = form.cleaned_data.get('factories')
        
        if not cities or not factories:
            form.add_error(None, 'Please select at least one city and one factory.')
            return self.form_invalid(form)
        
        # Additional validation - factories should already be filtered by clean() method
        if not factories:
            form.add_error('factories', 'No valid factories found for the selected cities.')
            return self.form_invalid(form)
        
        # Create a batch for each selected factory
        created_batches = []
        base_batch_number = form.cleaned_data.get('batch_number')
        wheat_amount = form.cleaned_data.get('wheat_amount')
        waste_factor = form.cleaned_data.get('waste_factor')
        expected_flour_output = form.cleaned_data.get('expected_flour_output')
        
        # Initialize notification service
        notification_service = BatchNotificationService()
        
        # Wrap batch creation in try-except for robust error handling
        try:
            for i, factory in enumerate(factories):
                # Generate unique batch number for each factory
                if len(factories) > 1:
                    batch_number = f"{base_batch_number}-{factory.name[:3].upper()}-{i+1:02d}"
                else:
                    batch_number = base_batch_number
                
                # Double-check if batch number already exists (race condition protection)
                if Batch.objects.filter(batch_number=batch_number).exists():
                    form.add_error('batch_number', f'Batch number "{batch_number}" already exists. Please choose a different number.')
                    return self.form_invalid(form)
                
                # Create batch with all required fields
                # Create batch with start date
                batch_data = {
                    'batch_number': batch_number,
                    'factory': factory,
                    'wheat_amount': wheat_amount,
                    'waste_factor': waste_factor,
                    'expected_flour_output': expected_flour_output,
                    'status': 'pending'
                }
                
                # If super admin is creating batch and start_date is provided, use it
                if is_super_admin(self.request.user) and form.cleaned_data.get('start_date'):
                    batch_data['start_date'] = form.cleaned_data['start_date']
                
                batch = Batch.objects.create(**batch_data)
                created_batches.append(batch)
                
                # Send notifications to responsible users
                try:
                    notification_service.notify_batch_created(batch)
                except Exception as notification_error:
                    # Log notification error but don't fail batch creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to send notification for batch {batch.batch_number}: {notification_error}')
                    
        except Exception as creation_error:
            # If any batch creation fails, clean up already created batches
            for created_batch in created_batches:
                try:
                    created_batch.delete()
                except:
                    pass
            
            # Add form error with helpful message
            form.add_error(None, f'Failed to create batch: {str(creation_error)}. Please try again with a different batch number.')
            return self.form_invalid(form)
        
        messages.success(self.request, f'Successfully created {len(created_batches)} batch(es).')
        
        # FIXED: Simple redirect to batch list (no need for complex success_url logic)
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(reverse_lazy('batch-list'))

class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'batches/batch_detail.html'
    context_object_name = 'batch'
    
    def get_queryset(self):
        # Optimize database queries with select_related and prefetch_related
        return super().get_queryset().select_related(
            'factory', 
            'factory__city', 
            'approved_by'
        ).prefetch_related(
            'factory__devices',
            'factory__responsible_users',
            'notifications',
            'flour_bag_counts'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.get_object()
        
        # Use the new BatchProductionService
        service = BatchProductionService()
        context['production_data'] = service.calculate_batch_progress(batch)
        context['analytics'] = service.get_batch_analytics(batch)
        
        # Get flour bag counts
        context['flour_bag_counts'] = FlourBagCount.objects.filter(batch=batch).order_by('-timestamp')[:10]
        
        # Get batch notifications
        context['notifications'] = BatchNotification.objects.filter(batch=batch).order_by('-sent_at')[:5]
        
        # Get device information
        if batch.factory:
            context['devices'] = batch.factory.devices.all()
        
        # Calculate today's production (daily production from today)
        from datetime import date
        today = date.today()
        today_production = 0
        
        if batch.factory and batch.factory.devices.exists():
            # Get today's production from ProductionData
            device = batch.factory.devices.first()
            today_production_data = ProductionData.objects.filter(
                device=device,
                created_at__date=today
            ).first()
            
            if today_production_data:
                today_production = today_production_data.daily_production
        
        # Calculate total production from start date to now
        total_production_units = batch.current_value or 0
        total_production_tons = total_production_units * 50 / 1000  # Convert to tons
        
        # Calculate remaining
        remaining_units = max(0, (batch.expected_flour_output * 1000 / 50) - total_production_units)
        remaining_tons = remaining_units * 50 / 1000
        
        # Add template variables for batch_detail.html with correct calculations
        context['yield_rate'] = batch.progress_percentage
        context['batch_start_date'] = batch.start_date
        context['today_production'] = today_production  # Today's daily production
        context['cumulative_units'] = total_production_units  # Total units from start to now
        context['cumulative_tons'] = total_production_tons  # Total tons from start to now
        context['remaining_units'] = remaining_units  # Remaining units needed
        context['remaining_tons'] = remaining_tons  # Remaining tons needed
        context['progress_percentage'] = batch.progress_percentage
        context['conversion_factor'] = 50  # kg per unit
        
        # Get production entries for the table
        context['production_entries'] = self._get_production_entries(batch)
        
        return context
    
    def _get_production_entries(self, batch):
        """Get production entries for the batch detail table"""
        entries = []
        if batch.factory and batch.factory.devices.exists():
            # Get production data for each day since batch start
            from django.db.models import Q
            from datetime import timedelta
            
            device = batch.factory.devices.first()
            production_data = ProductionData.objects.filter(
                device=device,
                created_at__gte=batch.start_date
            ).order_by('created_at')
            
            cumulative_value = 0
            for data in production_data:
                cumulative_value += data.daily_production
                entries.append({
                    'date': data.created_at.date(),
                    'start_value': cumulative_value - data.daily_production,
                    'end_value': cumulative_value,
                    'difference': data.daily_production,
                    'cumulative_tons': cumulative_value * 50 / 1000  # Convert to tons
                })
        
        return entries

class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'batches/batch_form.html'
    success_url = reverse_lazy('batch-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        batch = form.save(commit=False)
        
        # Only allow updates if batch can be edited
        if not batch.can_be_edited:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Batch {batch.batch_number} cannot be edited in its current status.'
                })
            messages.error(self.request, f'Batch {batch.batch_number} cannot be edited in its current status.')
            return self.form_invalid(form)
        
        # Check if start_date is being changed by super admin
        if 'start_date' in form.changed_data:
            if not is_super_admin(self.request.user):
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Only Super Admins can change batch start dates.'
                    })
                messages.error(self.request, 'Only Super Admins can change batch start dates.')
                return self.form_invalid(form)
            
            new_start_date = form.cleaned_data['start_date']
            try:
                # Update start date with historical data integration
                batch.update_start_date_with_historical_data(new_start_date, self.request.user)
                message = f'Batch {batch.batch_number} start date updated with historical data integration.'
            except ValueError as e:
                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f'Error updating start date: {str(e)}'
                    })
                messages.error(self.request, f'Error updating start date: {str(e)}')
                return self.form_invalid(form)
        else:
            # Normal save for other fields
            batch.save()
            message = f'Batch {batch.batch_number} updated successfully.'
        
        # Return JSON response for AJAX requests
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'batch_data': {
                    'wheat_amount': float(batch.wheat_amount),
                    'expected_flour_output': float(batch.expected_flour_output),
                    'actual_flour_output': float(batch.actual_flour_output),
                    'waste_factor': float(batch.waste_factor),
                    'progress_percentage': batch.progress_percentage,
                }
            })
        
        # Standard response for non-AJAX requests
        messages.success(self.request, message)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Return JSON response for AJAX requests
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            return JsonResponse({
                'success': False,
                'error': 'Form validation failed: ' + '; '.join(errors)
            })
        
        return super().form_invalid(form)

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
            
            # Use the new BatchProductionService
            service = BatchProductionService()
            result = service.update_batch_progress(batch)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': f'Batch {batch.batch_number} updated successfully',
                    'data': result['data']
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Unknown error occurred')
                }, status=400)
                
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class BatchStatusUpdateView(LoginRequiredMixin, View):
    """View for updating batch status"""
    
    def post(self, request, pk):
        if not is_super_admin(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Only Super Admins can update batch status'
            }, status=403)
        
        try:
            batch = Batch.objects.get(pk=pk)
            new_status = request.POST.get('status')
            
            if not new_status:
                return JsonResponse({
                    'success': False,
                    'error': 'Status is required'
                }, status=400)
            
            if new_status not in dict(Batch.STATUS_CHOICES):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid status'
                }, status=400)
            
            # Update status
            old_status = batch.status
            batch.status = new_status
            
            # Set approved_by and approved_at if status is approved
            if new_status == 'approved' and not batch.approved_by:
                batch.approved_by = request.user
                batch.approved_at = timezone.now()
            
            # Set end_date if completed
            if new_status == 'completed':
                batch.is_completed = True
                batch.end_date = timezone.now()
            
            batch.save()
            
            # Send notifications based on status change
            notification_service = BatchNotificationService()
            
            if new_status == 'approved' and old_status != 'approved':
                notification_service.notify_batch_approved(batch, request.user)
            elif new_status == 'in_process' and old_status != 'in_process':
                notification_service.notify_batch_started(batch, request.user)
            
            return JsonResponse({
                'success': True,
                'message': f'Batch {batch.batch_number} status updated from {old_status} to {new_status}',
                'new_status': new_status
            })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class BatchAnalyticsView(LoginRequiredMixin, DetailView):
    """View for detailed batch analytics"""
    model = Batch
    template_name = 'batches/batch_analytics.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.get_object()
        
        # Get comprehensive analytics
        service = BatchProductionService()
        context['analytics'] = service.get_batch_analytics(batch)
        
        return context

class BatchTemplateCreateView(LoginRequiredMixin, CreateView):
    """View for creating batch templates"""
    model = BatchTemplate
    template_name = 'batches/batch_template_form.html'
    fields = ['name', 'description', 'wheat_amount', 'waste_factor', 'expected_duration_days', 'applicable_factories', 'is_default']
    success_url = reverse_lazy('batch-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

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

class BatchApprovalView(LoginRequiredMixin, View):
    """View for responsible users to approve batches"""
    
    def get(self, request):
        # Get batches that need approval from this user
        notification_service = BatchNotificationService()
        pending_batches = notification_service.get_pending_batches_for_user(request.user)
        
        context = {
            'pending_batches': pending_batches,
            'user': request.user
        }
        return render(request, 'batches/batch_approval.html', context)
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                # Use select_for_update to prevent race conditions
                batch = Batch.objects.select_for_update().get(pk=pk)
                
                # Check if user is responsible for this factory
                if batch.factory not in request.user.responsible_factories.all():
                    return JsonResponse({
                        'success': False,
                        'error': 'You are not authorized to approve this batch'
                    }, status=403)
                
                # Check if batch is in pending status
                if batch.status != 'pending':
                    return JsonResponse({
                        'success': False,
                        'error': 'Batch is not in pending status'
                    }, status=400)
                
                # Approve the batch
                batch.status = 'approved'
                batch.approved_by = request.user
                batch.approved_at = timezone.now()
                batch.save()
                
                # Send notifications
                notification_service = BatchNotificationService()
                notification_service.notify_batch_approved(batch, request.user)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Batch {batch.batch_number} has been approved'
                })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class BatchStartView(LoginRequiredMixin, View):
    """View for responsible users to start approved batches"""
    
    def get(self, request):
        # Get approved batches that can be started by this user
        notification_service = BatchNotificationService()
        approved_batches = notification_service.get_approved_batches_for_user(request.user)
        
        context = {
            'approved_batches': approved_batches,
            'user': request.user
        }
        return render(request, 'batches/batch_start.html', context)
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                # Use select_for_update to prevent race conditions
                batch = Batch.objects.select_for_update().get(pk=pk)
                
                # Check if user is responsible for this factory
                if batch.factory not in request.user.responsible_factories.all():
                    return JsonResponse({
                        'success': False,
                        'error': 'You are not authorized to start this batch'
                    }, status=403)
                
                # Check if batch is in approved status
                if batch.status != 'approved':
                    return JsonResponse({
                        'success': False,
                        'error': 'Batch is not in approved status'
                    }, status=400)
                
                # Auto-complete previous batches for this factory
                batch.auto_complete_previous_batches()
                
                # Start the batch
                batch.status = 'in_process'
                batch.save()
                
                # Send notifications
                notification_service = BatchNotificationService()
                notification_service.notify_batch_started(batch, request.user)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Batch {batch.batch_number} has been started'
                })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class BatchStopView(LoginRequiredMixin, View):
    """View for responsible users to stop in-process batches"""
    
    def get(self, request):
        # Get in-process batches that can be stopped by this user
        notification_service = BatchNotificationService()
        in_process_batches = Batch.objects.filter(
            factory__in=request.user.responsible_factories.all(),
            status='in_process'
        ).order_by('-created_at')
        
        context = {
            'in_process_batches': in_process_batches,
            'user': request.user
        }
        return render(request, 'batches/batch_stop.html', context)
    
    def post(self, request, pk):
        try:
            with transaction.atomic():
                # Use select_for_update to prevent race conditions
                batch = Batch.objects.select_for_update().get(pk=pk)
                
                # Check if user is responsible for this factory
                if batch.factory not in request.user.responsible_factories.all():
                    return JsonResponse({
                        'success': False,
                        'error': 'You are not authorized to stop this batch'
                    }, status=403)
                
                # Check if batch is in in_process status
                if batch.status != 'in_process':
                    return JsonResponse({
                        'success': False,
                        'error': 'Batch is not in process'
                    }, status=400)
                
                # Stop the batch
                batch.status = 'completed'
                batch.is_completed = True
                batch.end_date = timezone.now()
                batch.save()
                
                # Send notifications
                notification_service = BatchNotificationService()
                notification_service.notify_batch_completed(batch, request.user)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Batch {batch.batch_number} has been stopped and completed'
                })
            
        except Batch.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Batch not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@login_required
def batch_delete(request, pk):
    """Delete a batch - only for super admins"""
    if not is_super_admin(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Only super admins can delete batches'
        }, status=403)
    
    try:
        batch = get_object_or_404(Batch, pk=pk)
        
        # Check if batch can be deleted (not in production)
        # Super admins can force delete any batch
        if batch.status in ['in_process', 'completed']:
            # Check if this is a force delete request
            force_delete = request.POST.get('force_delete', 'false').lower() == 'true'
            
            if not force_delete:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot delete batch in {batch.get_status_display()} status. Use force delete option.',
                    'can_force_delete': True
                }, status=400)
            else:
                # Log force delete for audit
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Super admin {request.user.username} force deleted batch {batch.batch_number} (ID: {batch.id}) in {batch.status} status')
        
        batch_number = batch.batch_number
        batch.delete()
        
        messages.success(request, f'Batch "{batch_number}" has been deleted successfully.')
        
        return JsonResponse({
            'success': True,
            'message': f'Batch "{batch_number}" deleted successfully'
        })
        
    except Batch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error deleting batch: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
def batch_bulk_delete(request):
    """Bulk delete batches - only for super admins"""
    if not is_super_admin(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Only super admins can delete batches'
        }, status=403)
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method allowed'
        }, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        batch_ids = data.get('batch_ids', [])
        
        if not batch_ids:
            return JsonResponse({
                'success': False,
                'error': 'No batch IDs provided'
            }, status=400)
        
        # Get batches that can be deleted
        deletable_batches = Batch.objects.filter(
            id__in=batch_ids,
            status__in=['pending', 'cancelled']  # Only allow deletion of pending/cancelled batches
        )
        
        non_deletable_batches = Batch.objects.filter(
            id__in=batch_ids
        ).exclude(
            id__in=deletable_batches.values_list('id', flat=True)
        )
        
        # Delete the batches
        deleted_count = deletable_batches.count()
        batch_numbers = list(deletable_batches.values_list('batch_number', flat=True))
        deletable_batches.delete()
        
        # Prepare response message
        if deleted_count > 0:
            success_message = f'Successfully deleted {deleted_count} batch(es): {", ".join(batch_numbers)}'
            if non_deletable_batches.exists():
                non_deletable_numbers = list(non_deletable_batches.values_list('batch_number', flat=True))
                success_message += f'\nCould not delete {non_deletable_batches.count()} batch(es) (in production): {", ".join(non_deletable_numbers)}'
            
            messages.success(request, success_message)
        
        return JsonResponse({
            'success': True,
            'message': f'Deleted {deleted_count} batch(es)',
            'deleted_count': deleted_count,
            'non_deletable_count': non_deletable_batches.count()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)