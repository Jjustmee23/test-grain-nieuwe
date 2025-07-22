from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from .profile_form import UserUpdateForm, CustomPasswordChangeForm, UserProfileForm, NotificationPreferenceForm
from mill.models import ContactTicket, UserProfile, Notification, EmailHistory, UserNotificationPreference, TwoFactorAuth
import qrcode
import base64
import secrets
import pyotp
from io import BytesIO

@login_required
def manage_profile(request):
    user = request.user
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, f'Profile updated successfully on {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
                return redirect('manage_profile')
            else:
                messages.error(request, 'Please correct the errors below.')
                # Initialize other forms for re-display
                password_form = CustomPasswordChangeForm(user)
                profile_form = UserProfileForm(instance=user_profile) if user_profile else UserProfileForm()
                notification_form = NotificationPreferenceForm(instance=notification_preferences) if notification_preferences else NotificationPreferenceForm()
        
        elif 'update_profile_info' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=user_profile)
            if profile_form.is_valid():
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
                messages.success(request, 'Team information updated successfully!')
                return redirect('manage_profile')
            else:
                messages.error(request, 'Please correct the errors in the profile form.')
                # Initialize other forms for re-display
                user_form = UserUpdateForm(instance=user)
                password_form = CustomPasswordChangeForm(user)
                notification_form = NotificationPreferenceForm(instance=notification_preferences) if notification_preferences else NotificationPreferenceForm()
        
        elif 'update_notifications' in request.POST:
            notification_form = NotificationPreferenceForm(request.POST, instance=notification_preferences)
            if notification_form.is_valid():
                notification_pref = notification_form.save(commit=False)
                notification_pref.user = user
                notification_pref.save()
                messages.success(request, 'Notification preferences updated successfully!')
                return redirect('manage_profile')
            else:
                messages.error(request, 'Please correct the errors in the notification form.')
                # Initialize other forms for re-display
                user_form = UserUpdateForm(instance=user)
                password_form = CustomPasswordChangeForm(user)
                profile_form = UserProfileForm(instance=user_profile) if user_profile else UserProfileForm()
        
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('manage_profile')
            else:
                messages.error(request, 'Please correct the errors in the password form.')
                # Initialize other forms for re-display
                user_form = UserUpdateForm(instance=user)
                profile_form = UserProfileForm(instance=user_profile) if user_profile else UserProfileForm()
                notification_form = NotificationPreferenceForm(instance=notification_preferences) if notification_preferences else NotificationPreferenceForm()
    # Get user profile information
    try:
        user_profile = UserProfile.objects.get(user=user)
        team = user_profile.team
        allowed_cities = user_profile.allowed_cities.all()
        allowed_factories = user_profile.allowed_factories.all()
        support_tickets_enabled = user_profile.support_tickets_enabled
    except UserProfile.DoesNotExist:
        user_profile = None
        team = None
        allowed_cities = []
        allowed_factories = []
        support_tickets_enabled = False
    
    # Get notification preferences
    try:
        notification_preferences = UserNotificationPreference.objects.get(user=user)
    except UserNotificationPreference.DoesNotExist:
        notification_preferences = None
    
    # Initialize forms
    if request.method == 'POST':
        # Forms will be initialized in the POST handling above
        pass
    else:
        user_form = UserUpdateForm(instance=user)
        password_form = CustomPasswordChangeForm(user)
        profile_form = UserProfileForm(instance=user_profile) if user_profile else UserProfileForm()
        notification_form = NotificationPreferenceForm(instance=notification_preferences) if notification_preferences else NotificationPreferenceForm()

    # Get user's tickets
    tickets = ContactTicket.objects.filter(created_by=user).order_by('-created_at')
    
    # Pagination for tickets
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check two-factor authentication status
    try:
        two_factor_auth = TwoFactorAuth.objects.get(user=user)
        two_factor_enabled = two_factor_auth.is_enabled
    except TwoFactorAuth.DoesNotExist:
        two_factor_enabled = False
    
    # Get user's notifications
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get user's email history
    email_history = EmailHistory.objects.filter(user=user).order_by('-sent_at')[:5]
    
    # Get user's activity log (admin actions)
    user_content_type = ContentType.objects.get_for_model(user)
    activity_logs = LogEntry.objects.filter(
        user=user
    ).order_by('-action_time')[:10]
    
    # Calculate additional statistics
    total_notifications = Notification.objects.filter(user=user).count()
    unread_notifications = Notification.objects.filter(user=user, read=False).count()
    total_emails = EmailHistory.objects.filter(user=user).count()
    
    # Get recent activity items
    recent_activities = []
    
    # Add profile update activity
    if user.date_joined:
        recent_activities.append({
            'type': 'profile_update',
            'title': 'Account Created',
            'description': 'Your account was created',
            'date': user.date_joined,
            'icon': 'bi-person-check',
            'color': 'bg-primary'
        })
    
    # Add last login activity
    if user.last_login:
        recent_activities.append({
            'type': 'login',
            'title': 'Last Login',
            'description': 'You last logged into the system',
            'date': user.last_login,
            'icon': 'bi-box-arrow-in-right',
            'color': 'bg-info'
        })
    
    # Add ticket activities
    if tickets.exists():
        latest_ticket = tickets.first()
        recent_activities.append({
            'type': 'ticket_created',
            'title': 'Latest Support Ticket',
            'description': f'Ticket #{latest_ticket.id} - {latest_ticket.subject}',
            'date': latest_ticket.created_at,
            'icon': 'bi-ticket-detailed',
            'color': 'bg-success'
        })
    
    # Add notification activities
    if notifications.exists():
        latest_notification = notifications.first()
        recent_activities.append({
            'type': 'notification',
            'title': 'Latest Notification',
            'description': latest_notification.title,
            'date': latest_notification.created_at,
            'icon': 'bi-bell',
            'color': 'bg-warning'
        })
    
    # Sort activities by date
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:5]
    
    context = {
        'user_form': user_form,
        'password_form': password_form,
        'profile_form': profile_form,
        'notification_form': notification_form,
        'last_update': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'current_user': user.username,
        'user': user,  # Add user object for template
        'tickets': page_obj,
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status__in=['NEW', 'IN_PROGRESS', 'PENDING']).count(),
        'resolved_tickets': tickets.filter(status__in=['RESOLVED', 'CLOSED']).count(),
        
        # User profile information
        'team': team,
        'allowed_cities': allowed_cities,
        'allowed_factories': allowed_factories,
        'support_tickets_enabled': support_tickets_enabled,
        
        # Notifications
        'notifications': notifications,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        
        # Email history
        'email_history': email_history,
        'total_emails': total_emails,
        
        # Activity logs
        'activity_logs': activity_logs,
        'recent_activities': recent_activities,
        
        # Two-factor authentication
        'two_factor_enabled': two_factor_enabled,
    }
    return render(request, 'accounts/manage_profile.html', context)

@login_required
def setup_2fa(request):
    """Setup 2FA for the current user"""
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enable':
            # Generate a new secret key
            secret_key = pyotp.random_base32()
            
            # Create or update 2FA record
            two_factor_auth, created = TwoFactorAuth.objects.get_or_create(
                user=user,
                defaults={'secret_key': secret_key, 'is_enabled': False}
            )
            if not created:
                two_factor_auth.secret_key = secret_key
                two_factor_auth.is_enabled = False
                two_factor_auth.save()
            
            # Generate QR code
            totp = pyotp.TOTP(secret_key)
            provisioning_uri = totp.provisioning_uri(
                name=user.username,
                issuer_name="Mill Management System"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return JsonResponse({
                'success': True,
                'qr_code': f'data:image/png;base64,{qr_code_base64}',
                'secret_key': secret_key,
                'device_id': two_factor_auth.id
            })
        
        elif action == 'verify':
            device_id = request.POST.get('device_id')
            token = request.POST.get('token')
            
            try:
                two_factor_auth = TwoFactorAuth.objects.get(id=device_id, user=user)
                totp = pyotp.TOTP(two_factor_auth.secret_key)
                
                if totp.verify(token):
                    two_factor_auth.is_enabled = True
                    two_factor_auth.save()
                    return JsonResponse({'success': True, 'message': '2FA enabled successfully!'})
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid verification code'})
            except TwoFactorAuth.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Device not found'})
        
        elif action == 'disable':
            try:
                two_factor_auth = TwoFactorAuth.objects.get(user=user)
                two_factor_auth.is_enabled = False
                two_factor_auth.save()
                return JsonResponse({'success': True, 'message': '2FA disabled successfully!'})
            except TwoFactorAuth.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'No 2FA device found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def get_2fa_status(request):
    """Get current 2FA status"""
    user = request.user
    
    try:
        two_factor_auth = TwoFactorAuth.objects.get(user=user)
        return JsonResponse({
            'enabled': two_factor_auth.is_enabled,
            'created_at': two_factor_auth.created_at.isoformat()
        })
    except TwoFactorAuth.DoesNotExist:
        return JsonResponse({'enabled': False})