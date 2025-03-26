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