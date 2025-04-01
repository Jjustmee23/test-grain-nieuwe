# notifications/context_processors.py
from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        return {'unread_notifications': Notification.objects.filter(
            user=request.user,
            read=False
        ).order_by('-timestamp')[:5]}
    return {}