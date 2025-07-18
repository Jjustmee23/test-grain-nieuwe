from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import transaction
from mill.models import Batch, Factory, FlourBagCount
from mill.forms import BatchForm
from mill.utils import is_super_admin , allowed_factories
from datetime import datetime
import logging

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

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Batch created successfully!')
        return super().form_valid(form)

class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'batches/batch_detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.get_object()
        context['flour_bag_counts'] = batch.flour_bag_counts.all().order_by('-timestamp')
        context['alerts'] = batch.alerts.all().order_by('-created_at')
        return context
logger = logging.getLogger(__name__)

class BatchUpdateView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk):
        try:
            batch = Batch.objects.select_for_update().get(pk=pk)
            
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
                batch.expected_flour_output = batch.wheat_amount * ((100 - batch.waste_factor) / 100)

            # Handle batch completion
            if is_completed and not batch.is_completed:
                batch.is_completed = True
                batch.end_date = timezone.now()
            
            # Record who made the changes
            batch.updated_by = request.user.username
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
                        
                    FlourBagCount.objects.create(
                        batch=batch,
                        bag_count=bag_count,
                        device=...,  # Ensure this is a valid Device instance

                        bags_weight=bags_weight,
                        timestamp=timezone.now(),
                        created_by=request.user 
                    )
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
                    'updated_by': batch.updated_by,
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