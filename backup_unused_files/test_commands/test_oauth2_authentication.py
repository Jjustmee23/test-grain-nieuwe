from django.core.management.base import BaseCommand
from django.conf import settings
from mill.models import Microsoft365Settings
from mill.services.notification_service import NotificationService
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test OAuth2 authentication and email sending with refresh tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Testing OAuth2 authentication with refresh tokens...')
        )

        # Get Microsoft 365 settings
        try:
            settings_obj = Microsoft365Settings.objects.get(is_active=True)
        except Microsoft365Settings.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('No Microsoft 365 settings found. Run setup_oauth2_authorization first.')
            )
            return

        # Display current configuration
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Current Configuration'))
        self.stdout.write('='*60)
        self.stdout.write(f'Client ID: {settings_obj.client_id}')
        self.stdout.write(f'Tenant ID: {settings_obj.tenant_id}')
        self.stdout.write(f'Auth User: {settings_obj.auth_user}')
        self.stdout.write(f'From Email: {settings_obj.from_email}')
        self.stdout.write(f'From Name: {settings_obj.from_name}')
        self.stdout.write(f'Has Access Token: {"Yes" if settings_obj.access_token else "No"}')
        self.stdout.write(f'Has Refresh Token: {"Yes" if settings_obj.refresh_token else "No"}')
        if settings_obj.token_expires_at:
            self.stdout.write(f'Token Expires: {settings_obj.token_expires_at}')

        # Test 1: Token Refresh
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('TEST 1: Token Refresh'))
        self.stdout.write('='*60)
        
        if not settings_obj.refresh_token:
            self.stdout.write(
                self.style.ERROR('❌ No refresh token found. Please run setup_oauth2_authorization first.')
            )
            return

        notification_service = NotificationService()
        access_token = notification_service._get_access_token()
        
        if access_token:
            self.stdout.write('✅ Access token retrieved successfully using refresh token!')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to get access token. Check your refresh token and configuration.')
            )
            return

        # Test 2: Graph API Connection
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('TEST 2: Graph API Connection'))
        self.stdout.write('='*60)
        
        success = self._test_graph_api_connection(settings_obj, access_token)
        
        if not success:
            self.stdout.write(
                self.style.ERROR('❌ Graph API connection failed. Check permissions and configuration.')
            )
            return

        # Test 3: Send Test Email
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('TEST 3: Send Test Email'))
        self.stdout.write('='*60)
        
        test_email = options['test_email'] or settings_obj.auth_user
        
        if not test_email:
            self.stdout.write(
                self.style.ERROR('❌ No test email provided. Use --test-email or configure auth_user.')
            )
            return

        self.stdout.write(f'Sending test email to: {test_email}')
        
        success = self._send_test_email(notification_service, test_email)
        
        if success:
            self.stdout.write('✅ Test email sent successfully!')
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 ALL TESTS PASSED!'))
            self.stdout.write('='*60)
            self.stdout.write('Your OAuth2 configuration is working correctly.')
            self.stdout.write('You can now send emails from the shared mailbox using delegated permissions.')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Test email failed. Check the error messages above.')
            )

    def _test_graph_api_connection(self, settings_obj, access_token):
        """Test connection to Microsoft Graph API"""
        try:
            # Test with a simple API call to get user info
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Try to get user info
            graph_url = f'https://graph.microsoft.com/v1.0/users/{settings_obj.auth_user}'
            
            self.stdout.write(f'Testing Graph API connection to: {graph_url}')
            
            response = requests.get(graph_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                user_data = response.json()
                self.stdout.write('✅ Graph API connection successful!')
                self.stdout.write(f'User: {user_data.get("displayName", "Unknown")}')
                self.stdout.write(f'Email: {user_data.get("mail", "Unknown")}')
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'Graph API connection failed: {response.status_code}')
                )
                self.stdout.write(f'Response: {response.text}')
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error'].get('message', 'Unknown error')
                        error_code = error_data['error'].get('code', 'Unknown')
                        self.stdout.write(f'Error code: {error_code}')
                        self.stdout.write(f'Error message: {error_msg}')
                        
                        if error_code == 'Request_ResourceNotFound':
                            self.stdout.write(
                                self.style.WARNING('User not found. Check if auth_user exists in your tenant.')
                            )
                        elif error_code == 'ErrorAccessDenied':
                            self.stdout.write(
                                self.style.WARNING('Access denied. Check delegated permissions.')
                            )
                except:
                    pass
                
                return False
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Request error: {e}')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
            return False

    def _send_test_email(self, notification_service, test_email):
        """Send a test email using the notification service"""
        try:
            # Create a test email history record
            from mill.models import EmailLog
            
            email_history = EmailLog.objects.create(
                to_email=test_email,
                subject='Test Email - OAuth2 Authentication',
                message='This is a test email to verify OAuth2 authentication with refresh tokens is working correctly.',
                status='pending'
            )
            
            # Send test email
            success = notification_service._send_direct_email(
                to_email=test_email,
                subject='Test Email - OAuth2 Authentication',
                message='''
                <html>
                <body>
                    <h2>Test Email - OAuth2 Authentication</h2>
                    <p>This is a test email to verify that OAuth2 authentication with refresh tokens is working correctly.</p>
                    <p><strong>Configuration:</strong></p>
                    <ul>
                        <li>Authentication: Semi-machine-to-machine with refresh tokens</li>
                        <li>Permissions: Delegated (not Application)</li>
                        <li>Shared Mailbox: Using SendAs permission</li>
                    </ul>
                    <p>If you receive this email, your configuration is working correctly!</p>
                    <hr>
                    <p><em>Sent by Mill Application</em></p>
                </body>
                </html>
                ''',
                email_history=email_history
            )
            
            # Update email history
            email_history.refresh_from_db()
            
            if email_history.status == 'sent':
                self.stdout.write('✅ Email sent successfully!')
                self.stdout.write(f'Email ID: {email_history.id}')
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Email failed: {email_history.error_message}')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending test email: {e}')
            )
            return False 