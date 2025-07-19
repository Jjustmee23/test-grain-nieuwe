import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import msal
import json
import requests
from typing import List, Dict, Optional, Union
from mill.models import (
    Notification, UserNotificationPreference, NotificationCategory,
    Microsoft365Settings, NotificationLog, EmailTemplate
)

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via in-app and email"""
    
    def __init__(self):
        self.ms365_settings = self._get_ms365_settings()
    
    def _get_ms365_settings(self) -> Optional[Microsoft365Settings]:
        """Get active Microsoft 365 settings"""
        try:
            return Microsoft365Settings.objects.filter(is_active=True).first()
        except Exception as e:
            logger.error(f"Error getting Microsoft 365 settings: {e}")
            return None
    
    def send_notification(
        self,
        user,
        category_name: str,
        title: str,
        message: str,
        priority: str = 'medium',
        link: str = None,
        related_batch=None,
        related_factory=None,
        related_device=None,
        force_email: bool = False
    ) -> Dict[str, bool]:
        """
        Send notification to user via in-app and/or email
        
        Returns:
            Dict with 'in_app_sent' and 'email_sent' boolean values
        """
        try:
            # Get or create user preferences
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'receive_in_app': True,
                    'receive_email': bool(user.email),
                    'email_address': user.email
                }
            )
            
            # Get notification category
            try:
                category = NotificationCategory.objects.get(name=category_name, is_active=True)
            except NotificationCategory.DoesNotExist:
                logger.error(f"Notification category '{category_name}' not found")
                return {'in_app_sent': False, 'email_sent': False}
            
            # Check if user has this category enabled
            if not force_email and category not in preferences.enabled_categories.all():
                logger.info(f"User {user.username} has category {category_name} disabled")
                return {'in_app_sent': False, 'email_sent': False}
            
            # Create notification record
            notification = Notification.objects.create(
                user=user,
                category=category,
                title=title,
                message=message,
                priority=priority,
                link=link,
                related_batch=related_batch,
                related_factory=related_factory,
                related_device=related_device
            )
            
            results = {'in_app_sent': False, 'email_sent': False}
            
            # Send in-app notification
            if preferences.receive_in_app:
                results['in_app_sent'] = self._send_in_app_notification(notification)
            
            # Send email notification
            if (preferences.receive_email and preferences.email_address) or force_email:
                results['email_sent'] = self._send_email_notification(notification, preferences)
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_in_app = results['in_app_sent']
            notification.sent_email = results['email_sent']
            notification.save()
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending notification to {user.username}: {e}")
            return {'in_app_sent': False, 'email_sent': False}
    
    def _send_in_app_notification(self, notification: Notification) -> bool:
        """Send in-app notification"""
        try:
            # In-app notifications are automatically created when the Notification object is saved
            # We just need to log the delivery
            NotificationLog.objects.create(
                notification=notification,
                delivery_method='app',
                status='success'
            )
            return True
        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            return False
    
    def _send_email_notification(self, notification: Notification, preferences: UserNotificationPreference) -> bool:
        """Send email notification using Microsoft 365 OAuth2 with refresh tokens"""
        try:
            if not self.ms365_settings:
                logger.error("No Microsoft 365 settings configured")
                return False
            
            # Get access token using refresh token
            access_token = self._get_access_token()
            if not access_token:
                logger.error("Failed to get access token")
                return False
            
            # Get email template
            template = self._get_email_template(notification.category)
            
            # Prepare email content
            email_content = self._prepare_email_content(notification, template)
            
            # Send email via Microsoft Graph API with delegated permissions
            success = self._send_via_graph_api(
                to_email=preferences.email_address,
                subject=email_content['subject'],
                html_content=email_content['html'],
                text_content=email_content['text']
            )
            
            if success:
                notification.email_sent_at = timezone.now()
                notification.save()
                
                NotificationLog.objects.create(
                    notification=notification,
                    delivery_method='email',
                    status='success'
                )
                return True
            else:
                NotificationLog.objects.create(
                    notification=notification,
                    delivery_method='email',
                    status='failed',
                    error_message='Failed to send via Graph API'
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            notification.email_error = str(e)
            notification.save()
            
            NotificationLog.objects.create(
                notification=notification,
                delivery_method='email',
                status='failed',
                error_message=str(e)
            )
            return False
    
    def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token using refresh token for delegated permissions"""
        try:
            if not self.ms365_settings:
                return None
            
            # Check if we have a valid token
            if (self.ms365_settings.access_token and 
                self.ms365_settings.token_expires_at and 
                self.ms365_settings.token_expires_at > timezone.now()):
                return self.ms365_settings.access_token
            
            # Try to refresh token
            if self.ms365_settings.refresh_token:
                return self._refresh_access_token()
            
            # No refresh token available - need initial authorization
            logger.error("No refresh token available. Please perform initial OAuth2 authorization.")
            return None
            
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    def _refresh_access_token(self) -> Optional[str]:
        """Refresh OAuth2 access token using refresh token for delegated permissions"""
        try:
            if not self.ms365_settings or not self.ms365_settings.refresh_token:
                return None
            
            logger.info("Refreshing access token using refresh token...")
            
            # Use refresh token to get new access token
            token_url = f"https://login.microsoftonline.com/{self.ms365_settings.tenant_id}/oauth2/v2.0/token"
            
            data = {
                'client_id': self.ms365_settings.client_id,
                'client_secret': self.ms365_settings.client_secret,
                'refresh_token': self.ms365_settings.refresh_token,
                'grant_type': 'refresh_token',
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update settings with new tokens
                self.ms365_settings.access_token = token_data['access_token']
                self.ms365_settings.refresh_token = token_data.get('refresh_token', self.ms365_settings.refresh_token)
                
                # Calculate expiration
                expires_in = token_data.get('expires_in', 3600)
                self.ms365_settings.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                self.ms365_settings.save()
                
                logger.info("Access token refreshed successfully using refresh token")
                return token_data['access_token']
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error refreshing token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None
    
    def _get_email_template(self, category: NotificationCategory) -> Optional[EmailTemplate]:
        """Get email template for notification category"""
        try:
            return EmailTemplate.objects.filter(
                category=category,
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error getting email template: {e}")
            return None
    
    def _prepare_email_content(self, notification: Notification, template: Optional[EmailTemplate]) -> Dict[str, str]:
        """Prepare email content with template or default"""
        if template:
            # Use template
            context = {
                'notification': notification,
                'user': notification.user,
                'category': notification.category,
                'timestamp': notification.created_at,
            }
            
            subject = template.subject
            html_content = render_to_string('emails/notification_template.html', context)
            text_content = template.text_content
        else:
            # Use default template
            subject = f"[{notification.category.name}] {notification.title}"
            html_content = render_to_string('emails/default_notification.html', {
                'notification': notification,
                'user': notification.user
            })
            text_content = f"{notification.title}\n\n{notification.message}"
        
        return {
            'subject': subject,
            'html': html_content,
            'text': text_content
        }
    
    def _send_via_graph_api(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via Microsoft Graph API with delegated permissions using refresh tokens"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                logger.error("No access token available for Graph API")
                return False
            
            # Get settings
            auth_user = self.ms365_settings.auth_user
            sender_email = self.ms365_settings.from_email
            
            logger.info(f"Attempting to send email via Graph API (Delegated):")
            logger.info(f"  Auth User: {auth_user}")
            logger.info(f"  From Email: {sender_email}")
            logger.info(f"  To Email: {to_email}")
            logger.info(f"  Subject: {subject}")
            
            # For delegated permissions, we can use SendAs to send from shared mailbox
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
            
            # Send via Graph API using delegated permissions
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Use the auth_user endpoint (danny.v@...) with SendAs permission for shared mailbox
            graph_url = f'https://graph.microsoft.com/v1.0/users/{auth_user}/sendMail'
            
            logger.info(f"Sending delegated request to: {graph_url}")
            logger.info(f"Message structure: {json.dumps(message, indent=2)}")
            
            response = requests.post(
                graph_url,
                headers=headers,
                json=message,
                timeout=30
            )
            
            logger.info(f"Graph API Response Status: {response.status_code}")
            logger.info(f"Graph API Response Headers: {dict(response.headers)}")
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully via Graph API (Delegated) from {sender_email} (auth: {auth_user}) to {to_email}")
                return True
            else:
                logger.error(f"Graph API error: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                logger.error(f"Attempted to send from: {sender_email} (auth: {auth_user}) to: {to_email}")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error'].get('message', 'Unknown error')
                        error_code = error_data['error'].get('code', 'Unknown')
                        logger.error(f"Graph API error code: {error_code}")
                        logger.error(f"Graph API error message: {error_msg}")
                        
                        # Provide specific guidance based on error code for delegated permissions
                        if error_code == 'ErrorAccessDenied':
                            logger.error("Delegated Access denied - check if user has 'Send As' permission for shared mailbox")
                        elif error_code == 'ErrorMailboxNotFound':
                            logger.error("Mailbox not found - check if the from_email address exists")
                        elif error_code == 'ErrorInvalidRequest':
                            logger.error("Invalid request - check message format and delegated permissions")
                        elif error_code == 'ErrorForbidden':
                            logger.error("Forbidden - user may not have sufficient delegated permissions")
                except:
                    pass
                
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Graph API request timed out")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending via Graph API (Delegated): {e}")
            return False
    
    def _send_direct_email(self, to_email: str, subject: str, message: str, email_history=None) -> bool:
        """Send direct email (not through notification system)"""
        try:
            if not self.ms365_settings:
                logger.error("No Microsoft 365 settings configured")
                if email_history:
                    email_history.status = 'failed'
                    email_history.error_message = "No Microsoft 365 settings configured"
                    email_history.save()
                return False
            
            # Get access token
            access_token = self._get_access_token()
            if not access_token:
                logger.error("Failed to get access token")
                if email_history:
                    email_history.status = 'failed'
                    email_history.error_message = "Failed to get access token"
                    email_history.save()
                return False
            
            # Send email via Microsoft Graph API
            success = self._send_via_graph_api(
                to_email=to_email,
                subject=subject,
                html_content=message,
                text_content=message
            )
            
            if success:
                if email_history:
                    email_history.status = 'sent'
                    email_history.save()
                return True
            else:
                # Get detailed error information from the Graph API call
                error_details = self._get_last_graph_api_error()
                if email_history:
                    email_history.status = 'failed'
                    email_history.error_message = error_details
                    email_history.save()
                return False
                
        except Exception as e:
            logger.error(f"Error sending direct email: {e}")
            if email_history:
                email_history.status = 'failed'
                email_history.error_message = str(e)
                email_history.save()
            return False
    
    def _get_last_graph_api_error(self) -> str:
        """Get the last Graph API error details for better error reporting"""
        try:
            # This method will be called after a failed Graph API call
            # We'll return a generic but helpful error message
            auth_user = self.ms365_settings.auth_user if self.ms365_settings else "unknown"
            from_email = self.ms365_settings.from_email if self.ms365_settings else "unknown"
            
            if auth_user != from_email:
                return f"Access denied - User {auth_user} does not have 'Send As' permission for shared mailbox {from_email}. Please grant permissions in Microsoft 365 Admin Center."
            else:
                return "Access denied - User does not have delegated 'Mail.Send' permission. Please check Azure AD app permissions."
        except Exception as e:
            return f"Unknown error occurred: {str(e)}"
    
    def send_bulk_notifications(
        self,
        users: List,
        category_name: str,
        title: str,
        message: str,
        priority: str = 'medium',
        link: str = None,
        related_batch=None,
        related_factory=None,
        related_device=None
    ) -> Dict[str, int]:
        """Send notifications to multiple users"""
        results = {'total': len(users), 'in_app_sent': 0, 'email_sent': 0, 'failed': 0}
        
        for user in users:
            try:
                result = self.send_notification(
                    user=user,
                    category_name=category_name,
                    title=title,
                    message=message,
                    priority=priority,
                    link=link,
                    related_batch=related_batch,
                    related_factory=related_factory,
                    related_device=related_device
                )
                
                if result['in_app_sent']:
                    results['in_app_sent'] += 1
                if result['email_sent']:
                    results['email_sent'] += 1
                if not result['in_app_sent'] and not result['email_sent']:
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error sending bulk notification to {user.username}: {e}")
                results['failed'] += 1
        
        return results
    
    def mark_notification_read(self, notification_id: int, user) -> bool:
        """Mark notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def get_user_notifications(self, user, limit: int = 50, unread_only: bool = False) -> List[Notification]:
        """Get notifications for user"""
        try:
            queryset = Notification.objects.filter(user=user)
            
            if unread_only:
                queryset = queryset.filter(read=False)
            
            return list(queryset[:limit])
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def get_unread_count(self, user) -> int:
        """Get count of unread notifications for user"""
        try:
            return Notification.objects.filter(user=user, read=False).count()
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0 