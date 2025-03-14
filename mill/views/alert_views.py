from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from mill.models import Alert
from django.shortcuts import get_object_or_404

from datetime import datetime

class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    template_name = 'alerts/alert_list.html'
    context_object_name = 'alerts'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'acknowledged':
            queryset = queryset.filter(is_acknowledged=True)
        
        return queryset

@login_required
def acknowledge_alert(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(Alert, id=alert_id)
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def alert_dashboard(request):
    active_alerts = Alert.objects.filter(
        is_active=True,
        is_acknowledged=False
    ).order_by('-created_at')

    critical_alerts = active_alerts.filter(severity='HIGH')
    warning_alerts = active_alerts.filter(severity='MEDIUM')
    
    context = {
        'critical_alerts': critical_alerts,
        'warning_alerts': warning_alerts,
        'total_active': active_alerts.count(),
    }
    
    return render(request, 'alerts/dashboard.html', context)