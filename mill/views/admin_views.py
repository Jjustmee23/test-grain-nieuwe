from django.utils.translation import get_language
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from mill.utils import superadmin_required, admin_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from mill.models import UserNotificationPreference, NotificationCategory, Notification, Microsoft365Settings, EmailHistory, MassMessage, EmailTemplate
from django.core.paginator import Paginator
import time
from django.utils import timezone

User = get_user_model()

@superadmin_required
def super_admin_view(request):
    current_locale = get_language()  # Gets the current language
    dir = 'rtl' if current_locale == 'ar' else 'ltr'
    return render(request, 'mill/super_admin.html', {'dir': dir, 'lang': current_locale})
@superadmin_required
def admin_view(request):
    context = {
        'user': request.user
    }
    return render(request, 'mill/admin.html', context)
@admin_required
def manage_admin_view(request):
    return render(request, 'mill/manage_admin.html')

@superadmin_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')  # Changed from 'admin_view' to 'dashboard'
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'mill/change_password.html', context)

@superadmin_required
def notification_management(request):
    """Notification management view for super admins"""
    try:
        # Get all users with their notification preferences
        users = User.objects.filter(is_active=True).prefetch_related(
            'usernotificationpreference',
            'usernotificationpreference__enabled_categories',
            'usernotificationpreference__mandatory_notifications',
            'groups'
        )
        
        # Get notification categories
        categories = NotificationCategory.objects.filter(is_active=True)
        
        # Get notification statistics
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        days = 30
        start_date = timezone.now() - timedelta(days=days)
        
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
        
        context = {
            'users': users,
            'categories': categories,
            'stats': {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'email_sent': email_sent,
                'period_days': days
            }
        }
        
        return render(request, 'mill/notification_management.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading notification management: {str(e)}')
        return redirect('admin')

@superadmin_required
def send_notification(request):
    """Send notification to users"""
    if request.method == 'POST':
        try:
            user_ids = request.POST.getlist('user_ids')
            category_name = request.POST.get('category_name')
            title = request.POST.get('title')
            message = request.POST.get('message')
            priority = request.POST.get('priority', 'medium')
            
            if not all([user_ids, category_name, title, message]):
                messages.error(request, 'All fields are required')
                return redirect('notification_management')
            
            # Get users
            users = User.objects.filter(id__in=user_ids, is_active=True)
            
            # Send notifications
            from mill.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            results = notification_service.send_bulk_notifications(
                users=list(users),
                category_name=category_name,
                title=title,
                message=message,
                priority=priority
            )
            
            messages.success(request, 
                f'Notifications sent successfully. '
                f'In-app: {results["in_app_sent"]}, '
                f'Email: {results["email_sent"]}, '
                f'Failed: {results["failed"]}'
            )
            
        except Exception as e:
            messages.error(request, f'Error sending notifications: {str(e)}')
    
    return redirect('notification_management')

@superadmin_required
def update_user_notification_preferences(request, user_id):
    """Update user notification preferences"""
    if request.method == 'POST':
        try:
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
            preferences.receive_in_app = request.POST.get('receive_in_app') == 'on'
            preferences.receive_email = request.POST.get('receive_email') == 'on'
            preferences.email_address = request.POST.get('email_address', user.email)
            preferences.can_modify_preferences = request.POST.get('can_modify_preferences') == 'on'
            
            # Update enabled categories
            enabled_categories = request.POST.getlist('enabled_categories')
            preferences.enabled_categories.set(enabled_categories)
            
            # Update mandatory categories
            mandatory_categories = request.POST.getlist('mandatory_categories')
            preferences.mandatory_notifications.set(mandatory_categories)
            
            preferences.save()
            
            messages.success(request, f'Notification preferences updated for {user.username}')
            
        except Exception as e:
            messages.error(request, f'Error updating preferences: {str(e)}')
    
    return redirect('notification_management')

@superadmin_required
def microsoft365_settings(request):
    """Manage Microsoft 365 OAuth2 settings"""
    try:
        settings_obj = Microsoft365Settings.objects.filter(is_active=True).first()
        
        if request.method == 'POST':
            if settings_obj:
                # Update existing settings
                settings_obj.client_id = request.POST.get('client_id')
                settings_obj.client_secret = request.POST.get('client_secret')
                settings_obj.tenant_id = request.POST.get('tenant_id')
                settings_obj.redirect_uri = request.POST.get('redirect_uri')
                settings_obj.auth_user = request.POST.get('auth_user')
                settings_obj.from_email = request.POST.get('from_email')
                settings_obj.from_name = request.POST.get('from_name', 'Mill Application')
                settings_obj.smtp_server = request.POST.get('smtp_server', 'smtp.office365.com')
                settings_obj.smtp_port = int(request.POST.get('smtp_port', 587))
                settings_obj.use_tls = request.POST.get('use_tls') == 'on'
                settings_obj.is_active = request.POST.get('is_active') == 'on'
            else:
                # Create new settings
                settings_obj = Microsoft365Settings.objects.create(
                    client_id=request.POST.get('client_id'),
                    client_secret=request.POST.get('client_secret'),
                    tenant_id=request.POST.get('tenant_id'),
                    redirect_uri=request.POST.get('redirect_uri'),
                    auth_user=request.POST.get('auth_user'),
                    from_email=request.POST.get('from_email'),
                    from_name=request.POST.get('from_name', 'Mill Application'),
                    smtp_server=request.POST.get('smtp_server', 'smtp.office365.com'),
                    smtp_port=int(request.POST.get('smtp_port', 587)),
                    use_tls=request.POST.get('use_tls') == 'on',
                    is_active=request.POST.get('is_active') == 'on'
                )
            
            settings_obj.save()
            messages.success(request, 'Microsoft 365 settings updated successfully')
            
        context = {
            'settings': settings_obj
        }
        
        return render(request, 'mill/microsoft365_settings.html', context)
        
    except Exception as e:
        messages.error(request, f'Error managing Microsoft 365 settings: {str(e)}')
        return redirect('admin')

@superadmin_required
def test_email_connection(request):
    """Test Microsoft 365 OAuth2 authentication with refresh tokens"""
    if request.method == 'POST':
        try:
            from mill.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Get Microsoft 365 settings for detailed feedback
            from mill.models import Microsoft365Settings
            ms365_settings = Microsoft365Settings.objects.filter(is_active=True).first()
            
            if not ms365_settings:
                messages.error(request, 'No active Microsoft 365 settings found. Please configure the settings first.')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Check if we have the required configuration
            missing_fields = []
            if not ms365_settings.client_id:
                missing_fields.append("Client ID")
            if not ms365_settings.client_secret:
                missing_fields.append("Client Secret")
            if not ms365_settings.tenant_id:
                missing_fields.append("Tenant ID")
            if not ms365_settings.auth_user:
                missing_fields.append("Auth User")
            if not ms365_settings.from_email:
                missing_fields.append("From Email")
            
            if missing_fields:
                messages.error(request, f'Missing required fields: {", ".join(missing_fields)}. Please complete the configuration.')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Check if we have a refresh token
            if not ms365_settings.refresh_token:
                messages.warning(request, 'No refresh token found. OAuth2 authorization is required.')
                messages.info(request, 'Please run: python manage.py setup_oauth2_authorization to start OAuth2 setup')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Try to get access token using refresh token
            access_token = notification_service._get_access_token()
            
            if access_token:
                # Check token expiration
                if ms365_settings.token_expires_at and ms365_settings.token_expires_at > timezone.now():
                    messages.success(request, f'✅ OAuth2 authentication successful!')
                    messages.info(request, f'Access token valid until: {ms365_settings.token_expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
                    messages.info(request, f'Auth User: {ms365_settings.auth_user}')
                    messages.info(request, f'From Email: {ms365_settings.from_email}')
                    messages.info(request, f'Authentication Method: Semi-machine-to-machine with refresh tokens')
                else:
                    messages.warning(request, '⚠️ Access token obtained but may be expired. Token refresh will be attempted automatically.')
                    messages.info(request, f'Token expires at: {ms365_settings.token_expires_at.strftime("%Y-%m-%d %H:%M:%S") if ms365_settings.token_expires_at else "Unknown"}')
            else:
                # Provide specific error information for OAuth2
                if not ms365_settings.refresh_token:
                    messages.error(request, '❌ OAuth2 authentication failed: No refresh token available')
                    messages.warning(request, 'Please complete OAuth2 authorization first:')
                    messages.info(request, '1. Run: python manage.py setup_oauth2_authorization')
                    messages.info(request, '2. Complete OAuth2 authorization in browser')
                    messages.info(request, '3. Run: python manage.py exchange_auth_code --auth-code YOUR_CODE')
                else:
                    messages.error(request, '❌ OAuth2 authentication failed: Could not refresh access token')
                    messages.warning(request, 'Possible causes:')
                    messages.info(request, '- Refresh token may be expired or invalid')
                    messages.info(request, '- Azure AD app permissions may be incorrect')
                    messages.info(request, '- Network connectivity issues')
                    messages.info(request, 'Try running: python manage.py setup_oauth2_authorization to re-authorize')
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messages.error(request, f'❌ OAuth2 authentication test failed: {str(e)}')
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'OAuth2 authentication test error: {error_details}')
    
    return redirect('admin:mill_microsoft365settings_changelist')

@superadmin_required
def test_email_send(request):
    """Send a test email using OAuth2 authentication with refresh tokens"""
    if request.method == 'POST':
        try:
            from mill.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Get current user's email for testing
            test_email = request.user.email
            if not test_email:
                messages.error(request, 'No email address found for current user. Please add an email address to your profile.')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Check if Microsoft 365 settings exist
            from mill.models import Microsoft365Settings
            ms365_settings = Microsoft365Settings.objects.filter(is_active=True).first()
            if not ms365_settings:
                messages.error(request, 'No active Microsoft 365 settings found. Please configure the settings first.')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Validate settings before sending
            validation_errors = []
            if not ms365_settings.auth_user:
                validation_errors.append("Auth User is required")
            if not ms365_settings.from_email:
                validation_errors.append("From Email is required")
            if not ms365_settings.client_id:
                validation_errors.append("Client ID is required")
            if not ms365_settings.client_secret:
                validation_errors.append("Client Secret is required")
            if not ms365_settings.tenant_id:
                validation_errors.append("Tenant ID is required")
            if not ms365_settings.refresh_token:
                validation_errors.append("Refresh Token is required (OAuth2 authorization needed)")
            
            if validation_errors:
                messages.error(request, f'Email settings validation failed: {", ".join(validation_errors)}')
                if "Refresh Token is required" in validation_errors:
                    messages.warning(request, 'Please complete OAuth2 authorization first:')
                    messages.info(request, '1. Run: python manage.py setup_oauth2_authorization')
                    messages.info(request, '2. Complete OAuth2 authorization in browser')
                    messages.info(request, '3. Run: python manage.py exchange_auth_code --auth-code YOUR_CODE')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Create test email content with OAuth2 information
            subject = "Test Email - OAuth2 Authentication (Semi-M2M)"
            message = f"""
            <html>
            <body>
                <h2>Test Email - OAuth2 Authentication</h2>
                <p>This is a test email to verify that the Microsoft 365 OAuth2 authentication with refresh tokens is working correctly.</p>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>Sent by: {request.user.username}</li>
                    <li>Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li>Authentication: OAuth2 with refresh tokens (Semi-machine-to-machine)</li>
                    <li>Auth User: {ms365_settings.auth_user}</li>
                    <li>From Email: {ms365_settings.from_email}</li>
                    <li>From Name: {ms365_settings.from_name}</li>
                    <li>Permissions: Delegated (not Application)</li>
                    <li>Shared Mailbox: Using SendAs permission</li>
                </ul>
                <p>If you received this email, the OAuth2 authentication and shared mailbox functionality is working properly!</p>
                <hr>
                <p><em>This is an automated test email from the Mill Application system using OAuth2 authentication.</em></p>
            </body>
            </html>
            """
            
            # Create email history record
            from mill.models import EmailHistory
            email_history = EmailHistory.objects.create(
                user=request.user,
                subject=subject,
                message=message,
                email_type='test',
                sent_by=request.user,
                status='pending'
            )
            
            # Try to get access token using refresh token
            access_token = notification_service._get_access_token()
            if not access_token:
                email_history.status = 'failed'
                email_history.error_message = 'Failed to obtain access token using refresh token'
                email_history.save()
                messages.error(request, '❌ Failed to obtain access token using refresh token.')
                messages.warning(request, 'Possible causes:')
                messages.info(request, '- Refresh token may be expired or invalid')
                messages.info(request, '- Azure AD app permissions may be incorrect')
                messages.info(request, '- Network connectivity issues')
                messages.info(request, 'Try running: python manage.py setup_oauth2_authorization to re-authorize')
                return redirect('admin:mill_microsoft365settings_changelist')
            
            # Log the attempt
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Attempting to send OAuth2 test email from {ms365_settings.auth_user} to {test_email}")
            
            # Send test email
            success = notification_service._send_direct_email(
                to_email=test_email,
                subject=subject,
                message=message,
                email_history=email_history
            )
            
            if success:
                email_history.status = 'sent'
                email_history.save()
                messages.success(request, f'✅ OAuth2 test email sent successfully to {test_email}!')
                messages.info(request, f'Check your inbox for the test email.')
                
                # Provide additional success information
                if ms365_settings.auth_user != ms365_settings.from_email:
                    messages.success(request, f'✅ Shared mailbox test successful: Auth user ({ms365_settings.auth_user}) sent email as ({ms365_settings.from_email})')
                else:
                    messages.success(request, f'✅ Regular mailbox test successful: Auth user and sender are the same ({ms365_settings.auth_user})')
                
                messages.info(request, f'Authentication Method: OAuth2 with refresh tokens (Semi-machine-to-machine)')
                messages.info(request, f'Permissions: Delegated permissions with SendAs for shared mailbox')
            else:
                email_history.status = 'failed'
                email_history.save()
                
                # Get detailed error information
                email_history.refresh_from_db()
                error_msg = email_history.error_message if email_history.error_message else 'Unknown error occurred'
                
                # Provide specific troubleshooting advice based on the error
                if 'access denied' in error_msg.lower():
                    if 'send as' in error_msg.lower():
                        messages.error(request, f'❌ Permission Error: {error_msg}')
                        messages.warning(request, 'To fix this:')
                        messages.info(request, '1. Go to Microsoft 365 Admin Center')
                        messages.info(request, '2. Groups → Shared mailboxes → Select noreply@nexonsolutions.be')
                        messages.info(request, '3. Members → Add danny.v@nexonsolutions.be')
                        messages.info(request, '4. Grant "Send As" permission')
                    else:
                        messages.error(request, f'❌ Permission Error: {error_msg}')
                        messages.warning(request, 'To fix this:')
                        messages.info(request, '1. Check Azure AD app permissions')
                        messages.info(request, '2. Ensure "Mail.Send" delegated permission is granted')
                        messages.info(request, '3. Grant admin consent for your organization')
                elif 'access token' in error_msg.lower():
                    messages.error(request, f'❌ Authentication failed: {error_msg}')
                    messages.warning(request, 'To fix this:')
                    messages.info(request, '1. Run: python manage.py setup_oauth2_authorization')
                    messages.info(request, '2. Complete OAuth2 authorization in browser')
                    messages.info(request, '3. Run: python manage.py exchange_auth_code --auth-code YOUR_CODE')
                elif 'timeout' in error_msg.lower():
                    messages.error(request, f'❌ Network timeout: {error_msg}')
                    messages.warning(request, 'Please check your internet connection and try again.')
                else:
                    messages.error(request, f'❌ Failed to send OAuth2 test email to {test_email}')
                    messages.error(request, f'Error: {error_msg}')
                
                # Provide general troubleshooting tips
                messages.warning(request, 'Troubleshooting:')
                messages.info(request, '1. Check Azure AD app permissions (Delegated: Mail.Send, User.Read)')
                messages.info(request, '2. Verify shared mailbox permissions in Microsoft 365 Admin Center')
                messages.info(request, '3. Ensure OAuth2 authorization is completed')
                messages.info(request, '4. Check network connectivity')
                
                # Log the detailed error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'OAuth2 test email failed with error: {error_msg}')
                logger.error(f'Email history ID: {email_history.id}')
                logger.error(f'Auth user: {ms365_settings.auth_user}')
                logger.error(f'From email: {ms365_settings.from_email}')
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messages.error(request, f'❌ OAuth2 test email failed: {str(e)}')
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'OAuth2 test email error: {error_details}')
    
    return redirect('admin:mill_microsoft365settings_changelist')

@superadmin_required
def email_history(request):
    """View email history for all users"""
    try:
        # Get email history with filters
        email_history = EmailHistory.objects.select_related('user', 'sent_by').all()
        
        # Apply filters
        user_filter = request.GET.get('user')
        email_type_filter = request.GET.get('email_type')
        status_filter = request.GET.get('status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        if user_filter:
            email_history = email_history.filter(user__username__icontains=user_filter)
        if email_type_filter:
            email_history = email_history.filter(email_type=email_type_filter)
        if status_filter:
            email_history = email_history.filter(status=status_filter)
        if date_from:
            email_history = email_history.filter(sent_at__gte=date_from)
        if date_to:
            email_history = email_history.filter(sent_at__lte=date_to)
        
        # Pagination
        paginator = Paginator(email_history, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'email_types': EmailHistory.email_type.field.choices,
            'status_choices': EmailHistory.status.field.choices,
            'filters': {
                'user': user_filter,
                'email_type': email_type_filter,
                'status': status_filter,
                'date_from': date_from,
                'date_to': date_to,
            }
        }
        
        return render(request, 'mill/email_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading email history: {str(e)}')
        return redirect('admin')

@superadmin_required
def user_email_history(request, user_id):
    """View email history for specific user"""
    try:
        user = get_object_or_404(User, id=user_id)
        email_history = EmailHistory.objects.filter(user=user).order_by('-sent_at')
        
        context = {
            'user': user,
            'email_history': email_history,
            'total_emails': email_history.count(),
            'sent_emails': email_history.filter(status='sent').count(),
            'failed_emails': email_history.filter(status='failed').count(),
        }
        
        return render(request, 'mill/user_email_history.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading user email history: {str(e)}')
        return redirect('email_history')

@superadmin_required
def send_direct_email(request, user_id):
    """Send direct email to specific user"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        if request.method == 'POST':
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            email_type = request.POST.get('email_type', 'custom')
            
            if not all([subject, message]):
                messages.error(request, 'Subject and message are required')
                return redirect('send_direct_email', user_id=user_id)
            
            # Create email history record
            email_history = EmailHistory.objects.create(
                user=user,
                subject=subject,
                message=message,
                email_type=email_type,
                sent_by=request.user,
                status='pending'
            )
            
            # Send email
            from mill.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            success = notification_service._send_direct_email(
                to_email=user.email,
                subject=subject,
                message=message,
                email_history=email_history
            )
            
            if success:
                email_history.status = 'sent'
                email_history.save()
                messages.success(request, f'Email sent successfully to {user.username}')
            else:
                email_history.status = 'failed'
                email_history.save()
                messages.error(request, f'Failed to send email to {user.username}')
            
            return redirect('user_email_history', user_id=user_id)
        
        context = {
            'user': user,
            'email_types': EmailHistory.email_type.field.choices,
        }
        
        return render(request, 'mill/send_direct_email.html', context)
        
    except Exception as e:
        messages.error(request, f'Error sending direct email: {str(e)}')
        return redirect('email_history')

@superadmin_required
def mass_messaging(request):
    """Mass messaging interface"""
    try:
        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            subject = request.POST.get('subject')
            target_groups = request.POST.getlist('target_groups')
            target_users = request.POST.getlist('target_users')
            
            if not all([title, message, subject]):
                messages.error(request, 'Title, message and subject are required')
                return redirect('mass_messaging')
            
            # Create mass message
            mass_message = MassMessage.objects.create(
                title=title,
                message=message,
                subject=subject,
                target_groups=target_groups,
                sent_by=request.user,
                status='draft'
            )
            
            # Get target users
            users = []
            if 'all' in target_groups:
                users = User.objects.filter(is_active=True)
            else:
                for group in target_groups:
                    if group == 'admin':
                        users.extend(User.objects.filter(groups__name='admin', is_active=True))
                    elif group == 'super_admin':
                        users.extend(User.objects.filter(is_superuser=True, is_active=True))
                    elif group == 'user':
                        users.extend(User.objects.filter(groups__name='user', is_active=True))
                
                # Add specific users
                if target_users:
                    specific_users = User.objects.filter(id__in=target_users, is_active=True)
                    users.extend(specific_users)
            
            # Remove duplicates
            users = list(set(users))
            mass_message.target_users.set(users)
            mass_message.total_recipients = len(users)
            mass_message.save()
            
            # Send emails
            from mill.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            mass_message.status = 'sending'
            mass_message.save()
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    # Create email history
                    email_history = EmailHistory.objects.create(
                        user=user,
                        subject=subject,
                        message=message,
                        email_type='mass_message',
                        sent_by=request.user,
                        mass_message_group=','.join(target_groups),
                        status='pending'
                    )
                    
                    # Send email
                    success = notification_service._send_direct_email(
                        to_email=user.email,
                        subject=subject,
                        message=message,
                        email_history=email_history
                    )
                    
                    if success:
                        email_history.status = 'sent'
                        email_history.save()
                        sent_count += 1
                    else:
                        email_history.status = 'failed'
                        email_history.save()
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
            
            mass_message.sent_count = sent_count
            mass_message.failed_count = failed_count
            mass_message.status = 'sent' if failed_count == 0 else 'failed'
            mass_message.save()
            
            messages.success(request, 
                f'Mass message sent successfully. '
                f'Sent: {sent_count}, Failed: {failed_count}, Total: {len(users)}'
            )
            
            return redirect('mass_messaging')
        
        # Get available users and groups
        users = User.objects.filter(is_active=True)
        admin_users = User.objects.filter(groups__name='admin', is_active=True)
        super_admin_users = User.objects.filter(is_superuser=True, is_active=True)
        regular_users = User.objects.filter(groups__name='user', is_active=True)
        
        # Get recent mass messages
        recent_messages = MassMessage.objects.all()[:10]
        
        context = {
            'users': users,
            'admin_users': admin_users,
            'super_admin_users': super_admin_users,
            'regular_users': regular_users,
            'recent_messages': recent_messages,
        }
        
        return render(request, 'mill/mass_messaging.html', context)
        
    except Exception as e:
        messages.error(request, f'Error with mass messaging: {str(e)}')
        return redirect('admin')

@superadmin_required
def email_templates(request):
    """Manage email templates"""
    try:
        if request.method == 'POST':
            template_id = request.POST.get('template_id')
            
            if template_id:
                # Update existing template
                template = get_object_or_404(EmailTemplate, id=template_id)
                template.name = request.POST.get('name')
                template.subject = request.POST.get('subject')
                template.html_content = request.POST.get('html_content')
                template.text_content = request.POST.get('text_content')
                template.template_type = request.POST.get('template_type')
                template.is_active = request.POST.get('is_active') == 'on'
            else:
                # Create new template
                template = EmailTemplate.objects.create(
                    name=request.POST.get('name'),
                    subject=request.POST.get('subject'),
                    html_content=request.POST.get('html_content'),
                    text_content=request.POST.get('text_content'),
                    template_type=request.POST.get('template_type'),
                    is_active=request.POST.get('is_active') == 'on'
                )
            
            template.save()
            messages.success(request, f'Template "{template.name}" saved successfully')
            
        templates = EmailTemplate.objects.all().order_by('template_type', 'name')
        
        context = {
            'templates': templates,
            'template_types': EmailTemplate.template_type.field.choices,
        }
        
        return render(request, 'mill/email_templates.html', context)
        
    except Exception as e:
        messages.error(request, f'Error managing email templates: {str(e)}')
        return redirect('admin')

@superadmin_required
def send_welcome_email(request, user_id):
    """Send welcome email to user"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get welcome template
        template = EmailTemplate.objects.filter(
            template_type='welcome',
            is_active=True
        ).first()
        
        if not template:
            messages.error(request, 'No welcome email template found')
            return redirect('user_email_history', user_id=user_id)
        
        # Prepare email content
        subject = template.subject.replace('{{ username }}', user.username)
        message = template.html_content.replace('{{ username }}', user.username)
        
        # Create email history
        email_history = EmailHistory.objects.create(
            user=user,
            subject=subject,
            message=message,
            email_type='welcome',
            sent_by=request.user,
            status='pending'
        )
        
        # Send email
        from mill.services.notification_service import NotificationService
        notification_service = NotificationService()
        
        success = notification_service._send_direct_email(
            to_email=user.email,
            subject=subject,
            message=message,
            email_history=email_history
        )
        
        if success:
            email_history.status = 'sent'
            email_history.save()
            messages.success(request, f'Welcome email sent to {user.username}')
        else:
            email_history.status = 'failed'
            email_history.save()
            messages.error(request, f'Failed to send welcome email to {user.username}')
        
        return redirect('user_email_history', user_id=user_id)
        
    except Exception as e:
        messages.error(request, f'Error sending welcome email: {str(e)}')
        return redirect('email_history')

@superadmin_required
def send_password_reset_email(request, user_id):
    """Send password reset email to user"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Get password reset template
        template = EmailTemplate.objects.filter(
            template_type='password_reset',
            is_active=True
        ).first()
        
        if not template:
            messages.error(request, 'No password reset email template found')
            return redirect('user_email_history', user_id=user_id)
        
        # Generate reset token (you can implement your own token generation)
        reset_token = f"reset_{user.id}_{int(time.time())}"
        
        # Prepare email content
        subject = template.subject.replace('{{ username }}', user.username)
        message = template.html_content.replace('{{ username }}', user.username)
        message = message.replace('{{ reset_link }}', f"http://yourdomain.com/reset-password/{reset_token}")
        
        # Create email history
        email_history = EmailHistory.objects.create(
            user=user,
            subject=subject,
            message=message,
            email_type='password_reset',
            sent_by=request.user,
            status='pending'
        )
        
        # Send email
        from mill.services.notification_service import NotificationService
        notification_service = NotificationService()
        
        success = notification_service._send_direct_email(
            to_email=user.email,
            subject=subject,
            message=message,
            email_history=email_history
        )
        
        if success:
            email_history.status = 'sent'
            email_history.save()
            messages.success(request, f'Password reset email sent to {user.username}')
        else:
            email_history.status = 'failed'
            email_history.save()
            messages.error(request, f'Failed to send password reset email to {user.username}')
        
        return redirect('user_email_history', user_id=user_id)
        
    except Exception as e:
        messages.error(request, f'Error sending password reset email: {str(e)}')
        return redirect('email_history')

