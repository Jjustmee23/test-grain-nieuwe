from django.core.management.base import BaseCommand
from django.conf import settings
from mill.models import Microsoft365Settings
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Exchange OAuth2 authorization code for access and refresh tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auth-code',
            type=str,
            required=True,
            help='Authorization code from OAuth2 callback'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Exchanging authorization code for tokens...')
        )

        # Get Microsoft 365 settings
        try:
            settings_obj = Microsoft365Settings.objects.get(is_active=True)
        except Microsoft365Settings.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('No Microsoft 365 settings found. Run setup_oauth2_authorization first.')
            )
            return

        auth_code = options['auth_code']
        
        # Exchange authorization code for tokens
        success = self._exchange_code_for_tokens(settings_obj, auth_code)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Authorization code exchanged successfully!')
            )
            self.stdout.write('Access token and refresh token have been saved.')
            self.stdout.write('\nYou can now test the configuration:')
            self.stdout.write(
                self.style.WARNING('python manage.py test_oauth2_authentication')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to exchange authorization code.')
            )
            self.stdout.write('Please check your configuration and try again.')

    def _exchange_code_for_tokens(self, settings_obj, auth_code):
        """Exchange authorization code for access and refresh tokens"""
        try:
            token_url = f"https://login.microsoftonline.com/{settings_obj.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': settings_obj.client_id,
                'client_secret': settings_obj.client_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': settings_obj.redirect_uri,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            self.stdout.write('Sending token exchange request...')
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Save tokens
                settings_obj.access_token = token_data['access_token']
                settings_obj.refresh_token = token_data.get('refresh_token', '')
                
                # Calculate expiration
                expires_in = token_data.get('expires_in', 3600)
                from django.utils import timezone
                from datetime import timedelta
                settings_obj.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                settings_obj.save()
                
                self.stdout.write('✅ Tokens received and saved successfully!')
                self.stdout.write(f'Access token expires at: {settings_obj.token_expires_at}')
                
                if settings_obj.refresh_token:
                    self.stdout.write('✅ Refresh token received - automatic token renewal enabled!')
                else:
                    self.stdout.write('⚠️  No refresh token received - manual re-authorization may be required')
                
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'Token exchange failed: {response.status_code}')
                )
                self.stdout.write(f'Response: {response.text}')
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                        error_desc = error_data.get('error_description', '')
                        self.stdout.write(f'Error: {error_msg}')
                        if error_desc:
                            self.stdout.write(f'Description: {error_desc}')
                        
                        # Provide specific guidance
                        if error_msg == 'invalid_grant':
                            self.stdout.write(
                                self.style.WARNING('Authorization code may be expired or already used.')
                            )
                        elif error_msg == 'invalid_client':
                            self.stdout.write(
                                self.style.WARNING('Check your client_id and client_secret.')
                            )
                        elif error_msg == 'invalid_redirect_uri':
                            self.stdout.write(
                                self.style.WARNING('Check your redirect_uri configuration.')
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