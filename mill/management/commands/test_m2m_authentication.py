from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from mill.models import Microsoft365Settings, EmailHistory
from mill.services.notification_service import NotificationService
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Microsoft 365 M2M (Machine-to-Machine) authentication configuration'

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
            
            self.stdout.write(self.style.SUCCESS('Microsoft 365 M2M Settings found:'))
            self.stdout.write(f'  Client ID: {ms365_settings.client_id[:20]}...')
            self.stdout.write(f'  Tenant ID: {ms365_settings.tenant_id}')
            self.stdout.write(f'  Auth User: {ms365_settings.auth_user}')
            self.stdout.write(f'  From Email: {ms365_settings.from_email}')
            self.stdout.write(f'  From Name: {ms365_settings.from_name}')
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
            
            # Test 1: Check if we can get access token using M2M
            self.stdout.write('Testing M2M access token generation...')
            access_token = notification_service._get_access_token()
            
            if access_token:
                self.stdout.write(
                    self.style.SUCCESS('✓ M2M access token generated successfully')
                )
                if verbose:
                    self.stdout.write(f'  Token: {access_token[:50]}...')
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to generate M2M access token')
                )
                return
            
            self.stdout.write('')

            # Test 2: Test email sending with M2M
            self.stdout.write('Testing M2M email sending...')
            
            # Create test email content
            subject = "Test Email - Mill Application (M2M Authentication)"
            message = f"""
            <html>
            <body>
                <h2>Test Email from Mill Application</h2>
                <p>This is a test email to verify that the Microsoft 365 M2M authentication is working correctly.</p>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li>Authentication: Microsoft 365 M2M (Machine-to-Machine)</li>
                    <li>Auth User: {ms365_settings.auth_user}</li>
                    <li>From Email: {ms365_settings.from_email}</li>
                    <li>From Name: {ms365_settings.from_name}</li>
                    <li>Flow: Client Credentials</li>
                </ul>
                <p>If you received this email, the M2M authentication is working properly!</p>
                <hr>
                <p><em>This is an automated test email from the Mill Application system using M2M authentication.</em></p>
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
                    self.style.SUCCESS(f'✓ M2M test email sent successfully to {test_email}!')
                )
                self.stdout.write('  Check your inbox for the test email.')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send M2M test email to {test_email}')
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
            
            # Test 3: Verify M2M configuration
            self.stdout.write('Verifying M2M configuration...')
            
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
                self.stdout.write(f'    This works for M2M but might not be a shared mailbox')
            
            # Check token expiration
            if ms365_settings.token_expires_at:
                if ms365_settings.token_expires_at > timezone.now():
                    self.stdout.write(f'  Token status: ✓ Valid (expires: {ms365_settings.token_expires_at})')
                else:
                    self.stdout.write(f'  Token status: ⚠ Expired (expired: {ms365_settings.token_expires_at})')
            else:
                self.stdout.write(f'  Token status: ⚠ No expiration set')
            
            self.stdout.write('')
            
            # Test 4: Provide M2M troubleshooting tips
            self.stdout.write('M2M Authentication Troubleshooting Tips:')
            self.stdout.write('  1. Ensure the Azure AD app has "Mail.Send" APPLICATION permission (not delegated)')
            self.stdout.write('  2. Check that admin consent has been granted for the application')
            self.stdout.write('  3. Verify that the client secret is valid and not expired')
            self.stdout.write('  4. Ensure the redirect URI is correctly configured in Azure AD')
            self.stdout.write('  5. Check Microsoft 365 admin center for any restrictions')
            self.stdout.write('  6. For shared mailboxes, ensure the app has "Send As" permission')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during M2M testing: {e}')
            )
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc()) 