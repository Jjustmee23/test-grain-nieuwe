from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from mill.models import Notification

@require_POST
@login_required
def mark_notification_read(request, pk):
    Notification.objects.filter(user=request.user, pk=pk).update(read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
@login_required
def delete_notification(request, pk):
    Notification.objects.filter(user=request.user, pk=pk).delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import transaction
from mill.models import Notification
from datetime import datetime
import logging

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    # ordering = ['-timestamp']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['factories'] = Factory.objects.filter(status=True)
    #     return context

class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'

@login_required
def mark_notification_read( request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if notification.read:
        messages.info(request, 'Notification already marked as read.')
        return redirect('notifications')
    notification.read = True
    notification.save()
    return redirect('notifications')

@login_required
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification:
        messages.error(request, 'Notification not found.')
        return redirect('notifications')
    notification.delete()
    return redirect('notifications')