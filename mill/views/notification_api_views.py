from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.db import transaction
import json
import logging
from typing import Dict, Any

from mill.models import (
    User, Notification, UserNotificationPreference, NotificationCategory,
    Microsoft365Settings, NotificationLog
)
from mill.services.notification_service import NotificationService
from mill.utils import superadmin_required, admin_required

logger = logging.getLogger(__name__)

class NotificationAPIView(View):
    """Base class for notification API views"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notification_service = NotificationService()

@method_decorator(csrf_exempt, name='dispatch')
class SendNotificationView(NotificationAPIView):
    """API endpoint to send notifications"""
    
    @method_decorator(login_required)
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['user_ids', 'category_name', 'title', 'message']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Check permissions
            if not (request.user.is_superuser or request.user.groups.filter(name='admin').exists()):
                return JsonResponse({
                    'success': False,
                    'error': 'Insufficient permissions to send notifications'
                }, status=403)
            
            # Get users
            user_ids = data['user_ids']
            if isinstance(user_ids, int):
                user_ids = [user_ids]
            
            users = User.objects.filter(id__in=user_ids)
            if not users.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No valid users found'
                }, status=400)
            
            # Send notifications
            results = self.notification_service.send_bulk_notifications(
                users=list(users),
                category_name=data['category_name'],
                title=data['title'],
                message=data['message'],
                priority=data.get('priority', 'medium'),
                link=data.get('link'),
                related_batch_id=data.get('related_batch_id'),
                related_factory_id=data.get('related_factory_id'),
                related_device_id=data.get('related_device_id')
            )
            
            return JsonResponse({
                'success': True,
                'results': results
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UserPreferencesView(NotificationAPIView):
    """API endpoint for user notification preferences"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Get user notification preferences"""
        try:
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=request.user,
                defaults={
                    'receive_in_app': True,
                    'receive_email': bool(request.user.email),
                    'email_address': request.user.email
                }
            )
            
            # Get available categories
            categories = NotificationCategory.objects.filter(is_active=True)
            
            return JsonResponse({
                'success': True,
                'preferences': {
                    'receive_in_app': preferences.receive_in_app,
                    'receive_email': preferences.receive_email,
                    'email_address': preferences.email_address,
                    'email_verified': preferences.email_verified,
                    'can_modify_preferences': preferences.can_modify_preferences,
                    'enabled_categories': list(preferences.enabled_categories.values_list('id', flat=True)),
                    'mandatory_categories': list(preferences.mandatory_notifications.values_list('id', flat=True)),
                    'is_admin': preferences.is_admin,
                    'is_super_admin': preferences.is_super_admin
                },
                'categories': [
                    {
                        'id': cat.id,
                        'name': cat.name,
                        'description': cat.description,
                        'notification_type': cat.notification_type,
                        'requires_admin': cat.requires_admin,
                        'requires_super_admin': cat.requires_super_admin
                    }
                    for cat in categories
                ]
            })
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @method_decorator(login_required)
    def post(self, request):
        """Update user notification preferences"""
        try:
            data = json.loads(request.body)
            
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=request.user,
                defaults={
                    'receive_in_app': True,
                    'receive_email': bool(request.user.email),
                    'email_address': request.user.email
                }
            )
            
            # Check if user can modify preferences
            if not preferences.can_modify_preferences:
                return JsonResponse({
                    'success': False,
                    'error': 'You cannot modify your notification preferences'
                }, status=403)
            
            # Update preferences
            if 'receive_in_app' in data:
                preferences.receive_in_app = data['receive_in_app']
            
            if 'receive_email' in data:
                preferences.receive_email = data['receive_email']
            
            if 'email_address' in data:
                preferences.email_address = data['email_address']
                preferences.email_verified = False  # Reset verification when email changes
            
            # Update enabled categories (only if not mandatory)
            if 'enabled_categories' in data:
                enabled_categories = data['enabled_categories']
                if isinstance(enabled_categories, list):
                    # Remove mandatory categories from the list
                    mandatory_categories = preferences.mandatory_notifications.all()
                    enabled_categories = [cat_id for cat_id in enabled_categories 
                                        if cat_id not in mandatory_categories.values_list('id', flat=True)]
                    
                    preferences.enabled_categories.set(enabled_categories)
            
            preferences.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Preferences updated successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UserNotificationsView(NotificationAPIView):
    """API endpoint for user notifications"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Get user notifications"""
        try:
            limit = int(request.GET.get('limit', 50))
            unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
            
            notifications = self.notification_service.get_user_notifications(
                user=request.user,
                limit=limit,
                unread_only=unread_only
            )
            
            unread_count = self.notification_service.get_unread_count(request.user)
            
            return JsonResponse({
                'success': True,
                'notifications': [
                    {
                        'id': notif.id,
                        'title': notif.title,
                        'message': notif.message,
                        'category': notif.category.name,
                        'priority': notif.priority,
                        'read': notif.read,
                        'link': notif.link,
                        'created_at': notif.created_at.isoformat(),
                        'sent_in_app': notif.sent_in_app,
                        'sent_email': notif.sent_email
                    }
                    for notif in notifications
                ],
                'unread_count': unread_count
            })
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @method_decorator(login_required)
    def post(self, request):
        """Mark notification as read"""
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            if not notification_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing notification_id'
                }, status=400)
            
            success = self.notification_service.mark_notification_read(
                notification_id=notification_id,
                user=request.user
            )
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Notification marked as read'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Notification not found'
                }, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AdminNotificationManagementView(NotificationAPIView):
    """API endpoint for admin notification management"""
    
    @method_decorator(superadmin_required)
    def get(self, request):
        """Get all users and their notification preferences"""
        try:
            users = User.objects.filter(is_active=True).prefetch_related(
                'usernotificationpreference',
                'usernotificationpreference__enabled_categories',
                'usernotificationpreference__mandatory_notifications',
                'groups'
            )
            
            categories = NotificationCategory.objects.filter(is_active=True)
            
            return JsonResponse({
                'success': True,
                'users': [
                    {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_active': user.is_active,
                        'is_superuser': user.is_superuser,
                        'groups': list(user.groups.values_list('name', flat=True)),
                        'preferences': {
                            'receive_in_app': getattr(user.usernotificationpreference, 'receive_in_app', True),
                            'receive_email': getattr(user.usernotificationpreference, 'receive_email', False),
                            'email_address': getattr(user.usernotificationpreference, 'email_address', user.email),
                            'can_modify_preferences': getattr(user.usernotificationpreference, 'can_modify_preferences', True),
                            'enabled_categories': list(getattr(user.usernotificationpreference, 'enabled_categories', []).values_list('id', flat=True)),
                            'mandatory_categories': list(getattr(user.usernotificationpreference, 'mandatory_notifications', []).values_list('id', flat=True)),
                            'is_admin': getattr(user.usernotificationpreference, 'is_admin', False),
                            'is_super_admin': getattr(user.usernotificationpreference, 'is_super_admin', False)
                        }
                    }
                    for user in users
                ],
                'categories': [
                    {
                        'id': cat.id,
                        'name': cat.name,
                        'description': cat.description,
                        'notification_type': cat.notification_type,
                        'requires_admin': cat.requires_admin,
                        'requires_super_admin': cat.requires_super_admin
                    }
                    for cat in categories
                ]
            })
            
        except Exception as e:
            logger.error(f"Error getting admin notification data: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    
    @method_decorator(superadmin_required)
    def post(self, request):
        """Update user notification preferences (admin)"""
        try:
            data = json.loads(request.body)
            
            user_id = data.get('user_id')
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing user_id'
                }, status=400)
            
            user = get_object_or_404(User, id=user_id)
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'receive_in_app': True,
                    'receive_email': bool(user.email),
                    'email_address': user.email
                }
            )
            
            # Update preferences
            if 'receive_in_app' in data:
                preferences.receive_in_app = data['receive_in_app']
            
            if 'receive_email' in data:
                preferences.receive_email = data['receive_email']
            
            if 'email_address' in data:
                preferences.email_address = data['email_address']
            
            if 'can_modify_preferences' in data:
                preferences.can_modify_preferences = data['can_modify_preferences']
            
            if 'enabled_categories' in data:
                enabled_categories = data['enabled_categories']
                if isinstance(enabled_categories, list):
                    preferences.enabled_categories.set(enabled_categories)
            
            if 'mandatory_categories' in data:
                mandatory_categories = data['mandatory_categories']
                if isinstance(mandatory_categories, list):
                    preferences.mandatory_notifications.set(mandatory_categories)
            
            preferences.save()
            
            return JsonResponse({
                'success': True,
                'message': 'User preferences updated successfully'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating user preferences (admin): {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class NotificationStatsView(NotificationAPIView):
    """API endpoint for notification statistics"""
    
    @method_decorator(admin_required)
    def get(self, request):
        """Get notification statistics"""
        try:
            from django.db.models import Count, Q
            from django.utils import timezone
            from datetime import timedelta
            
            # Get date range
            days = int(request.GET.get('days', 30))
            start_date = timezone.now() - timedelta(days=days)
            
            # Get statistics
            total_notifications = Notification.objects.filter(
                created_at__gte=start_date
            ).count()
            
            unread_notifications = Notification.objects.filter(
                created_at__gte=start_date,
                read=False
            ).count()
            
            email_sent = Notification.objects.filter(
                created_at__gte=start_date,
                sent_email=True
            ).count()
            
            in_app_sent = Notification.objects.filter(
                created_at__gte=start_date,
                sent_in_app=True
            ).count()
            
            # Get delivery statistics
            delivery_stats = NotificationLog.objects.filter(
                sent_at__gte=start_date
            ).values('delivery_method', 'status').annotate(
                count=Count('id')
            )
            
            return JsonResponse({
                'success': True,
                'stats': {
                    'total_notifications': total_notifications,
                    'unread_notifications': unread_notifications,
                    'email_sent': email_sent,
                    'in_app_sent': in_app_sent,
                    'delivery_stats': list(delivery_stats)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500) 