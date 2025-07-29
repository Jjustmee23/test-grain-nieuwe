from django.core.management.base import BaseCommand
from django.conf import settings
from mill.models import Microsoft365Settings
import requests
import webbrowser
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Set up OAuth2 authorization for Microsoft 365 email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Azure AD Application Client ID'
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Azure AD Application Client Secret'
        )
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Azure AD Tenant ID'
        )
        parser.add_argument(
            '--auth-user',
            type=str,
            help='User email for authentication (e.g., danny.v@...)'
        )
        parser.add_argument(
            '--from-email',
            type=str,
            help='Shared mailbox email (e.g., noreply@...)'
        )
        parser.add_argument(
            '--from-name',
            type=str,
            default='Mill Application',
            help='From name for emails'
        )
        parser.add_argument(
            '--redirect-uri',
            type=str,
            default='http://localhost:8000/auth/callback',
            help='OAuth2 redirect URI'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up OAuth2 authorization for Microsoft 365...')
        )

        # Get or create Microsoft 365 settings
        settings_obj, created = Microsoft365Settings.objects.get_or_create(
            is_active=True,
            defaults={
                'client_id': options['client_id'] or '',
                'client_secret': options['client_secret'] or '',
                'tenant_id': options['tenant_id'] or '',
                'auth_user': options['auth_user'] or '',
                'from_email': options['from_email'] or '',
                'from_name': options['from_name'],
                'redirect_uri': options['redirect_uri']
            }
        )

        if not created:
            # Update existing settings
            if options['client_id']:
                settings_obj.client_id = options['client_id']
            if options['client_secret']:
                settings_obj.client_secret = options['client_secret']
            if options['tenant_id']:
                settings_obj.tenant_id = options['tenant_id']
            if options['auth_user']:
                settings_obj.auth_user = options['auth_user']
            if options['from_email']:
                settings_obj.from_email = options['from_email']
            if options['from_name']:
                settings_obj.from_name = options['from_name']
            if options['redirect_uri']:
                settings_obj.redirect_uri = options['redirect_uri']
            settings_obj.save()

        # Validate required fields
        required_fields = ['client_id', 'client_secret', 'tenant_id', 'auth_user', 'from_email']
        missing_fields = [field for field in required_fields if not getattr(settings_obj, field)]
        
        if missing_fields:
            self.stdout.write(
                self.style.ERROR(f'Missing required fields: {", ".join(missing_fields)}')
            )
            self.stdout.write(
                self.style.WARNING('Please provide all required fields using --client-id, --client-secret, etc.')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Configuration saved successfully!')
        )
        self.stdout.write(f'Client ID: {settings_obj.client_id}')
        self.stdout.write(f'Tenant ID: {settings_obj.tenant_id}')
        self.stdout.write(f'Auth User: {settings_obj.auth_user}')
        self.stdout.write(f'From Email: {settings_obj.from_email}')
        self.stdout.write(f'Redirect URI: {settings_obj.redirect_uri}')

        # Generate authorization URL
        auth_url = self._generate_auth_url(settings_obj)
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('STEP 1: OAuth2 Authorization'))
        self.stdout.write('='*60)
        self.stdout.write(
            'Please follow these steps to complete OAuth2 authorization:'
        )
        self.stdout.write('\n1. Open the authorization URL in your browser:')
        self.stdout.write(self.style.WARNING(auth_url))
        
        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            self.stdout.write('Browser opened automatically.')
        except:
            self.stdout.write('Please copy and paste the URL into your browser manually.')
        
        self.stdout.write('\n2. Sign in with your Microsoft account (danny.v@...)')
        self.stdout.write('3. Grant the requested permissions')
        self.stdout.write('4. Copy the authorization code from the redirect URL')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('STEP 2: Exchange Authorization Code'))
        self.stdout.write('='*60)
        self.stdout.write(
            'After you get the authorization code, run this command:'
        )
        self.stdout.write(
            self.style.WARNING(
                f'python manage.py exchange_auth_code --auth-code YOUR_AUTH_CODE'
            )
        )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('STEP 3: Configure Permissions'))
        self.stdout.write('='*60)
        self.stdout.write(
            'Make sure the following permissions are configured:'
        )
        self.stdout.write('\nAzure AD App Permissions (Delegated):')
        self.stdout.write('- Mail.Send')
        self.stdout.write('- User.Read')
        
        self.stdout.write('\nMicrosoft 365 Admin Center:')
        self.stdout.write(f'- Add {settings_obj.auth_user} as member of {settings_obj.from_email}')
        self.stdout.write(f'- Grant "Send As" permission to {settings_obj.auth_user} for {settings_obj.from_email}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('STEP 4: Test Configuration'))
        self.stdout.write('='*60)
        self.stdout.write(
            'After completing all steps, test the configuration:'
        )
        self.stdout.write(
            self.style.WARNING('python manage.py test_oauth2_authentication')
        )

    def _generate_auth_url(self, settings_obj):
        """Generate OAuth2 authorization URL"""
        base_url = f"https://login.microsoftonline.com/{settings_obj.tenant_id}/oauth2/v2.0/authorize"
        
        params = {
            'client_id': settings_obj.client_id,
            'response_type': 'code',
            'redirect_uri': settings_obj.redirect_uri,
            'scope': 'https://graph.microsoft.com/.default',
            'response_mode': 'query',
            'state': 'oauth2_setup'
        }
        
        # Build URL with parameters
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}" 