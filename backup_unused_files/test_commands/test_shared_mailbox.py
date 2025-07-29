from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from mill.models import Microsoft365Settings, EmailHistory
from mill.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Microsoft 365 shared mailbox configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to (defaults to superuser email)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        # Get Microsoft 365 settings
        try:
            ms365_settings = Microsoft365Settings.objects.filter(is_active=True).first()
            if not ms365_settings:
                self.stdout.write(
                    self.style.ERROR('No active Microsoft 365 settings found. Please configure the settings first.')
                )
                return
            
            self.stdout.write(self.style.SUCCESS('Microsoft 365 Settings found:'))
            self.stdout.write(f'  Client ID: {ms365_settings.client_id[:20]}...')
            self.stdout.write(f'  Tenant ID: {ms365_settings.tenant_id}')
            self.stdout.write(f'  Auth User: {ms365_settings.auth_user}')
            self.stdout.write(f'  From Email: {ms365_settings.from_email}')
            self.stdout.write(f'  From Name: {ms365_settings.from_name}')
            self.stdout.write(f'  SMTP Server: {ms365_settings.smtp_server}:{ms365_settings.smtp_port}')
            self.stdout.write(f'  Use TLS: {ms365_settings.use_tls}')
            self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting Microsoft 365 settings: {e}')
            )
            return

        # Get test email address
        test_email = options['email']
        if not test_email:
            # Try to get superuser email
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser and superuser.email:
                test_email = superuser.email
            else:
                self.stdout.write(
                    self.style.ERROR('No email address provided and no superuser email found. Please provide an email address.')
                )
                return

        self.stdout.write(f'Test email address: {test_email}')
        self.stdout.write('')

        # Test notification service
        try:
            notification_service = NotificationService()
            
            # Test 1: Check if we can get access token
            self.stdout.write('Testing access token generation...')
            access_token = notification_service._get_access_token()
            
            if access_token:
                self.stdout.write(
                    self.style.SUCCESS('✓ Access token generated successfully')
                )
                if verbose:
                    self.stdout.write(f'  Token: {access_token[:50]}...')
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to generate access token')
                )
                return
            
            self.stdout.write('')

            # Test 2: Test email sending
            self.stdout.write('Testing email sending...')
            
            # Create test email content
            subject = "Test Email - Mill Application (Shared Mailbox)"
            message = f"""
            <html>
            <body>
                <h2>Test Email from Mill Application</h2>
                <p>This is a test email to verify that the Microsoft 365 shared mailbox integration is working correctly.</p>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li>Email service: Microsoft 365 OAuth2</li>
                    <li>Auth User: {ms365_settings.auth_user}</li>
                    <li>From Email: {ms365_settings.from_email}</li>
                    <li>From Name: {ms365_settings.from_name}</li>
                </ul>
                <p>If you received this email, the shared mailbox functionality is working properly!</p>
                <hr>
                <p><em>This is an automated test email from the Mill Application system.</em></p>
            </body>
            </html>
            """
            
            # Create email history record
            user = User.objects.filter(email=test_email).first() or User.objects.filter(is_superuser=True).first()
            email_history = EmailHistory.objects.create(
                user=user,
                subject=subject,
                message=message,
                email_type='test',
                sent_by=user,
                status='pending'
            )
            
            # Send test email
            success = notification_service._send_direct_email(
                to_email=test_email,
                subject=subject,
                message=message,
                email_history=email_history
            )
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Test email sent successfully to {test_email}!')
                )
                self.stdout.write('  Check your inbox for the test email.')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send test email to {test_email}')
                )
                
                # Check email history for error details
                email_history.refresh_from_db()
                if email_history.error_message:
                    self.stdout.write(f'  Error: {email_history.error_message}')
                
                # Check notification logs for more details
                from mill.models import NotificationLog
                recent_logs = NotificationLog.objects.filter(
                    delivery_method='email',
                    status='failed'
                ).order_by('-sent_at')[:5]
                
                if recent_logs:
                    self.stdout.write('  Recent email failures:')
                    for log in recent_logs:
                        self.stdout.write(f'    - {log.sent_at}: {log.error_message}')
            
            self.stdout.write('')
            
            # Test 3: Verify settings
            self.stdout.write('Verifying configuration...')
            
            # Check if auth_user has necessary permissions
            if '@' in ms365_settings.auth_user:
                self.stdout.write(f'  Auth user format: ✓ Valid email format')
            else:
                self.stdout.write(f'  Auth user format: ⚠ Should be an email address')
            
            # Check if from_email is different from auth_user (shared mailbox scenario)
            if ms365_settings.auth_user != ms365_settings.from_email:
                self.stdout.write(f'  Shared mailbox: ✓ Auth user and sender email are different')
                self.stdout.write(f'    Auth: {ms365_settings.auth_user}')
                self.stdout.write(f'    Sender: {ms365_settings.from_email}')
            else:
                self.stdout.write(f'  Shared mailbox: ⚠ Auth user and sender email are the same')
                self.stdout.write(f'    This might work for regular mailboxes but not shared mailboxes')
            
            # Check token expiration
            if ms365_settings.token_expires_at:
                if ms365_settings.token_expires_at > timezone.now():
                    self.stdout.write(f'  Token status: ✓ Valid (expires: {ms365_settings.token_expires_at})')
                else:
                    self.stdout.write(f'  Token status: ⚠ Expired (expired: {ms365_settings.token_expires_at})')
            else:
                self.stdout.write(f'  Token status: ⚠ No expiration set')
            
            self.stdout.write('')
            
            # Test 4: Provide troubleshooting tips
            self.stdout.write('Troubleshooting Tips:')
            self.stdout.write('  1. Ensure the auth_user has "Mail.Send" permission in Microsoft 365')
            self.stdout.write('  2. For shared mailboxes, the auth_user must have "Send As" permission')
            self.stdout.write('  3. Check that the application has the correct API permissions in Azure AD')
            self.stdout.write('  4. Verify that the client secret is valid and not expired')
            self.stdout.write('  5. Ensure the redirect URI is correctly configured in Azure AD')
            self.stdout.write('  6. Check Microsoft 365 admin center for any restrictions')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during testing: {e}')
            )
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc()) 