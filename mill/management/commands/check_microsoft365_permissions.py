from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from mill.models import Microsoft365Settings
from mill.services.notification_service import NotificationService
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check Microsoft 365 permissions and diagnose access issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-permissions',
            action='store_true',
            help='Provide instructions to fix permission issues'
        )

    def handle(self, *args, **options):
        fix_permissions = options['fix_permissions']
        
        # Get Microsoft 365 settings
        try:
            ms365_settings = Microsoft365Settings.objects.filter(is_active=True).first()
            if not ms365_settings:
                self.stdout.write(
                    self.style.ERROR('No active Microsoft 365 settings found.')
                )
                return
            
            self.stdout.write(self.style.SUCCESS('Microsoft 365 Settings found:'))
            self.stdout.write(f'  Auth User: {ms365_settings.auth_user}')
            self.stdout.write(f'  From Email: {ms365_settings.from_email}')
            self.stdout.write(f'  Client ID: {ms365_settings.client_id[:20]}...')
            self.stdout.write(f'  Tenant ID: {ms365_settings.tenant_id}')
            self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting Microsoft 365 settings: {e}')
            )
            return

        # Test notification service
        try:
            notification_service = NotificationService()
            
            # Test 1: Check access token
            self.stdout.write('Testing access token...')
            access_token = notification_service._get_access_token()
            
            if access_token:
                self.stdout.write(
                    self.style.SUCCESS('✓ Access token obtained successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Failed to obtain access token')
                )
                return
            
            # Test 2: Check user permissions via Graph API
            self.stdout.write('')
            self.stdout.write('Checking user permissions...')
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Check if auth_user can access their own mailbox
            try:
                response = requests.get(
                    f'https://graph.microsoft.com/v1.0/users/{ms365_settings.auth_user}/mailboxSettings',
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Auth user mailbox accessible')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Auth user mailbox not accessible: {response.status_code}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error checking auth user mailbox: {e}')
                )
            
            # Test 3: Check if auth_user can send emails
            self.stdout.write('')
            self.stdout.write('Testing email sending permissions...')
            
            # Create a simple test message
            test_message = {
                "message": {
                    "subject": "Permission Test",
                    "body": {
                        "contentType": "Text",
                        "content": "This is a permission test email."
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": ms365_settings.auth_user  # Send to self for testing
                            }
                        }
                    ]
                }
            }
            
            try:
                response = requests.post(
                    f'https://graph.microsoft.com/v1.0/users/{ms365_settings.auth_user}/sendMail',
                    headers=headers,
                    json=test_message,
                    timeout=10
                )
                
                if response.status_code == 202:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Auth user can send emails')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Auth user cannot send emails: {response.status_code}')
                    )
                    if response.text:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                            self.stdout.write(f'  Error: {error_msg}')
                        except:
                            self.stdout.write(f'  Response: {response.text}')
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error testing email sending: {e}')
                )
            
            # Test 4: Check shared mailbox permissions
            if ms365_settings.auth_user != ms365_settings.from_email:
                self.stdout.write('')
                self.stdout.write('Checking shared mailbox permissions...')
                
                # Try to send as shared mailbox
                shared_message = {
                    "message": {
                        "subject": "Shared Mailbox Permission Test",
                        "body": {
                            "contentType": "Text",
                            "content": "This is a shared mailbox permission test."
                        },
                        "toRecipients": [
                            {
                                "emailAddress": {
                                    "address": ms365_settings.auth_user
                                }
                            }
                        ],
                        "from": {
                            "emailAddress": {
                                "address": ms365_settings.from_email,
                                "name": ms365_settings.from_name
                            }
                        }
                    }
                }
                
                try:
                    response = requests.post(
                        f'https://graph.microsoft.com/v1.0/users/{ms365_settings.auth_user}/sendMail',
                        headers=headers,
                        json=shared_message,
                        timeout=10
                    )
                    
                    if response.status_code == 202:
                        self.stdout.write(
                            self.style.SUCCESS('✓ Can send as shared mailbox')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Cannot send as shared mailbox: {response.status_code}')
                        )
                        if response.text:
                            try:
                                error_data = response.json()
                                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                                error_code = error_data.get('error', {}).get('code', 'Unknown')
                                self.stdout.write(f'  Error Code: {error_code}')
                                self.stdout.write(f'  Error: {error_msg}')
                            except:
                                self.stdout.write(f'  Response: {response.text}')
                                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error testing shared mailbox: {e}')
                    )
            
            # Provide troubleshooting information
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Troubleshooting Information:'))
            
            if ms365_settings.auth_user != ms365_settings.from_email:
                self.stdout.write('  This is a shared mailbox configuration.')
                self.stdout.write(f'  Auth User: {ms365_settings.auth_user}')
                self.stdout.write(f'  Shared Mailbox: {ms365_settings.from_email}')
                self.stdout.write('')
                self.stdout.write('  Required Permissions:')
                self.stdout.write('    1. Auth user must have "Mail.Send" permission')
                self.stdout.write('    2. Auth user must have "Send As" permission for the shared mailbox')
                self.stdout.write('    3. Azure AD app must have "Mail.Send" application permission')
                self.stdout.write('')
                
                if fix_permissions:
                    self.stdout.write(self.style.SUCCESS('How to fix shared mailbox permissions:'))
                    self.stdout.write('  1. Go to Microsoft 365 Admin Center')
                    self.stdout.write('  2. Navigate to Groups > Shared mailboxes')
                    self.stdout.write('  3. Select the shared mailbox: ' + ms365_settings.from_email)
                    self.stdout.write('  4. Go to "Members" tab')
                    self.stdout.write('  5. Add user: ' + ms365_settings.auth_user)
                    self.stdout.write('  6. Grant "Send As" permission')
                    self.stdout.write('  7. Wait 15-30 minutes for permissions to propagate')
                    self.stdout.write('')
                    self.stdout.write('  Alternative: Use PowerShell to grant permissions:')
                    self.stdout.write('    Add-RecipientPermission -Identity "' + ms365_settings.from_email + '" -Trustee "' + ms365_settings.auth_user + '" -AccessRights SendAs')
            else:
                self.stdout.write('  This is a regular mailbox configuration.')
                self.stdout.write('  Auth user and sender email are the same.')
                self.stdout.write('')
                self.stdout.write('  Required Permissions:')
                self.stdout.write('    1. User must have "Mail.Send" permission')
                self.stdout.write('    2. Azure AD app must have "Mail.Send" application permission')
            
            self.stdout.write('')
            self.stdout.write('  Azure AD App Permissions:')
            self.stdout.write('    1. Go to Azure Portal > Azure Active Directory')
            self.stdout.write('    2. Navigate to App registrations')
            self.stdout.write('    3. Select your app: ' + ms365_settings.client_id[:20] + '...')
            self.stdout.write('    4. Go to "API permissions"')
            self.stdout.write('    5. Ensure "Mail.Send" permission is granted')
            self.stdout.write('    6. Click "Grant admin consent" if needed')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during permission check: {e}')
            )
            import traceback
            self.stdout.write(traceback.format_exc()) 