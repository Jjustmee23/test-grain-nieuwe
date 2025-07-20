import requests
import logging
from django.utils import timezone
from datetime import timedelta
from mill.models import Microsoft365Settings, EmailHistory

logger = logging.getLogger(__name__)

class SimpleEmailService:
    """Simple email service for Microsoft 365 OAuth2"""
    
    def __init__(self):
        self.settings = Microsoft365Settings.objects.filter(is_active=True).first()
    
    def get_access_token(self):
        """Get access token using refresh token"""
        if not self.settings or not self.settings.refresh_token:
            return None
        
        # Check if token is still valid
        if (self.settings.access_token and 
            self.settings.token_expires_at and 
            self.settings.token_expires_at > timezone.now()):
            return self.settings.access_token
        
        # Refresh token
        try:
            token_url = f"https://login.microsoftonline.com/{self.settings.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.settings.client_id,
                'client_secret': self.settings.client_secret,
                'refresh_token': self.settings.refresh_token,
                'grant_type': 'refresh_token',
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update settings
                self.settings.access_token = token_data['access_token']
                self.settings.refresh_token = token_data.get('refresh_token', self.settings.refresh_token)
                
                # Calculate expiration
                expires_in = token_data.get('expires_in', 3600)
                self.settings.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 300)
                self.settings.save()
                
                logger.info("Access token refreshed successfully")
                return token_data['access_token']
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def send_email(self, to_email, subject, html_content, text_content=None, user=None, sent_by=None):
        """Send email via Microsoft Graph API"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False, "No access token available"
            
            # Create email history record only if user is provided
            email_history = None
            if user:
                email_history = EmailHistory.objects.create(
                    user=user,
                    subject=subject,
                    message=html_content,
                    email_type='notification',
                    sent_by=sent_by,
                    status='pending'
                )
            
            # Send via Graph API
            graph_url = f"https://graph.microsoft.com/v1.0/users/{self.settings.auth_user}/sendMail"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": html_content
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(graph_url, headers=headers, json=message, timeout=30)
            
            if response.status_code == 202:
                if email_history:
                    email_history.status = 'sent'
                    email_history.save()
                logger.info(f"Email sent successfully to {to_email}")
                return True, "Email sent successfully"
            else:
                error_msg = f"Graph API error: {response.status_code} - {response.text}"
                if email_history:
                    email_history.status = 'failed'
                    email_history.error_message = error_msg
                    email_history.save()
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error sending email: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_connection(self):
        """Test OAuth2 connection"""
        if not self.settings:
            return False, "No Microsoft 365 settings found"
        
        # Check required fields
        required_fields = ['client_id', 'client_secret', 'tenant_id', 'auth_user', 'from_email']
        missing_fields = [field for field in required_fields if not getattr(self.settings, field)]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        if not self.settings.refresh_token:
            return False, "No refresh token found. OAuth2 authorization required."
        
        # Try to get access token
        access_token = self.get_access_token()
        if access_token:
            return True, f"Connection successful. Token valid until {self.settings.token_expires_at}"
        else:
            return False, "Failed to get access token"
    
    def test_email_send(self, test_email):
        """Send test email"""
        subject = "Test Email - Simple OAuth2"
        html_content = f"""
        <html>
        <body>
            <h2>Test Email - Simple OAuth2</h2>
            <p>This is a test email to verify OAuth2 authentication is working.</p>
            <p><strong>Details:</strong></p>
            <ul>
                <li>Auth User: {self.settings.auth_user}</li>
                <li>From Email: {self.settings.from_email}</li>
                <li>Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            <p>If you receive this, OAuth2 is working correctly!</p>
        </body>
        </html>
        """
        
        return self.send_email(test_email, subject, html_content, user=None, sent_by=None) 