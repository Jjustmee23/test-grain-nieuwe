import logging
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from ..models import (
    Batch, BatchNotification, Notification, NotificationCategory, 
    UserNotificationPreference, Factory, EmailHistory
)
from ..services.simple_email_service import SimpleEmailService

logger = logging.getLogger(__name__)

class BatchNotificationService:
    """
    Service for handling batch-related notifications
    """
    
    def __init__(self):
        self.email_service = SimpleEmailService()
    
    def notify_batch_created(self, batch):
        """
        Notify responsible users when a batch is created
        """
        try:
            if not batch.factory:
                logger.warning(f"Batch {batch.batch_number} has no factory assigned")
                return
            
            responsible_users = batch.factory.responsible_users.all()
            
            if not responsible_users:
                logger.info(f"No responsible users for factory {batch.factory.name}")
                return
            
            # Create notification category if it doesn't exist
            category, created = NotificationCategory.objects.get_or_create(
                notification_type='batch_assignment',
                defaults={
                    'name': 'Batch Assignment',
                    'description': 'Notifications for new batch assignments'
                }
            )
            
            # Create in-app notifications
            for user in responsible_users:
                # Check user preferences
                try:
                    user_prefs = UserNotificationPreference.objects.get(user=user)
                    if not user_prefs.receive_in_app:
                        continue
                except UserNotificationPreference.DoesNotExist:
                    # Default to in-app notifications
                    pass
                
                # Create notification
                notification = Notification.objects.create(
                    user=user,
                    category=category,
                    title=f"New Batch Assigned: {batch.batch_number}",
                    message=f"A new batch '{batch.batch_number}' has been assigned to {batch.factory.name}. "
                           f"Wheat amount: {batch.wheat_amount} tons, Expected output: {batch.expected_flour_output} tons.",
                    priority='medium',
                    status='pending',
                    related_batch=batch,
                    related_factory=batch.factory,
                    link=f"/batches/{batch.pk}/"
                )
                
                # Mark as sent in-app
                notification.sent_in_app = True
                notification.status = 'sent'
                notification.save()
                
                logger.info(f"Created in-app notification for user {user.username} about batch {batch.batch_number}")
            
            # Send email notifications
            self._send_batch_created_emails(batch, responsible_users)
            
            # Create batch notification record
            batch_notification = BatchNotification.objects.create(
                batch=batch,
                notification_type='batch_created',
                message=f"Batch {batch.batch_number} created and assigned to {batch.factory.name}"
            )
            batch_notification.sent_to.set(responsible_users)
            
            logger.info(f"Successfully notified {len(responsible_users)} users about batch {batch.batch_number}")
            
        except Exception as e:
            logger.error(f"Error notifying batch creation: {str(e)}")
    
    def notify_batch_approved(self, batch, approved_by):
        """
        Notify responsible users when a batch is approved
        """
        try:
            if not batch.factory:
                return
            
            responsible_users = batch.factory.responsible_users.all()
            
            if not responsible_users:
                return
            
            # Create notification category if it doesn't exist
            category, created = NotificationCategory.objects.get_or_create(
                notification_type='batch_approval',
                defaults={
                    'name': 'Batch Approval',
                    'description': 'Notifications for batch approvals'
                }
            )
            
            # Create in-app notifications
            for user in responsible_users:
                try:
                    user_prefs = UserNotificationPreference.objects.get(user=user)
                    if not user_prefs.receive_in_app:
                        continue
                except UserNotificationPreference.DoesNotExist:
                    pass
                
                notification = Notification.objects.create(
                    user=user,
                    category=category,
                    title=f"Batch Approved: {batch.batch_number}",
                    message=f"Batch '{batch.batch_number}' has been approved by {approved_by.get_full_name() or approved_by.username}. "
                           f"You can now start production.",
                    priority='high',
                    status='pending',
                    related_batch=batch,
                    related_factory=batch.factory,
                    link=f"/batches/{batch.pk}/"
                )
                
                notification.sent_in_app = True
                notification.status = 'sent'
                notification.save()
            
            # Send email notifications
            self._send_batch_approved_emails(batch, responsible_users, approved_by)
            
            # Create batch notification record
            batch_notification = BatchNotification.objects.create(
                batch=batch,
                notification_type='batch_approved',
                message=f"Batch {batch.batch_number} approved by {approved_by.get_full_name() or approved_by.username}"
            )
            batch_notification.sent_to.set(responsible_users)
            
            logger.info(f"Successfully notified {len(responsible_users)} users about batch approval {batch.batch_number}")
            
        except Exception as e:
            logger.error(f"Error notifying batch approval: {str(e)}")
    
    def notify_batch_started(self, batch, started_by):
        """
        Notify responsible users when a batch is started
        """
        try:
            if not batch.factory:
                return
            
            responsible_users = batch.factory.responsible_users.all()
            
            if not responsible_users:
                return
            
            # Create notification category if it doesn't exist
            category, created = NotificationCategory.objects.get_or_create(
                notification_type='batch_completion',
                defaults={
                    'name': 'Batch Completion',
                    'description': 'Notifications for batch status changes'
                }
            )
            
            # Create in-app notifications
            for user in responsible_users:
                try:
                    user_prefs = UserNotificationPreference.objects.get(user=user)
                    if not user_prefs.receive_in_app:
                        continue
                except UserNotificationPreference.DoesNotExist:
                    pass
                
                notification = Notification.objects.create(
                    user=user,
                    category=category,
                    title=f"Production Started: {batch.batch_number}",
                    message=f"Production has started for batch '{batch.batch_number}'. "
                           f"Counter tracking is now active.",
                    priority='medium',
                    status='pending',
                    related_batch=batch,
                    related_factory=batch.factory,
                    link=f"/batches/{batch.pk}/"
                )
                
                notification.sent_in_app = True
                notification.status = 'sent'
                notification.save()
            
            # Send email notifications
            self._send_batch_started_emails(batch, responsible_users, started_by)
            
            # Create batch notification record
            batch_notification = BatchNotification.objects.create(
                batch=batch,
                notification_type='batch_started',
                message=f"Batch {batch.batch_number} started by {started_by.get_full_name() or started_by.username}"
            )
            batch_notification.sent_to.set(responsible_users)
            
            logger.info(f"Successfully notified {len(responsible_users)} users about batch start {batch.batch_number}")
            
        except Exception as e:
            logger.error(f"Error notifying batch start: {str(e)}")
    
    def notify_batch_completed(self, batch, completed_by):
        """
        Notify responsible users when a batch is completed
        """
        try:
            if not batch.factory:
                return
            
            responsible_users = batch.factory.responsible_users.all()
            
            if not responsible_users:
                return
            
            # Create notification category if it doesn't exist
            category, created = NotificationCategory.objects.get_or_create(
                notification_type='batch_completion',
                defaults={
                    'name': 'Batch Completion',
                    'description': 'Notifications for batch status changes'
                }
            )
            
            # Create in-app notifications
            for user in responsible_users:
                try:
                    user_prefs = UserNotificationPreference.objects.get(user=user)
                    if not user_prefs.receive_in_app:
                        continue
                except UserNotificationPreference.DoesNotExist:
                    pass
                
                notification = Notification.objects.create(
                    user=user,
                    category=category,
                    title=f"Batch Completed: {batch.batch_number}",
                    message=f"Batch '{batch.batch_number}' has been completed. "
                           f"Production has finished.",
                    priority='high',
                    status='pending',
                    related_batch=batch,
                    related_factory=batch.factory,
                    link=f"/batches/{batch.pk}/"
                )
                
                notification.sent_in_app = True
                notification.status = 'sent'
                notification.save()
            
            # Send email notifications
            self._send_batch_completed_emails(batch, responsible_users, completed_by)
            
            # Create batch notification record
            batch_notification = BatchNotification.objects.create(
                batch=batch,
                notification_type='batch_completed',
                message=f"Batch {batch.batch_number} completed by {completed_by.get_full_name() or completed_by.username}"
            )
            batch_notification.sent_to.set(responsible_users)
            
            logger.info(f"Successfully notified {len(responsible_users)} users about batch completion {batch.batch_number}")
            
        except Exception as e:
            logger.error(f"Error notifying batch completion: {str(e)}")
    
    def _send_batch_created_emails(self, batch, users):
        """
        Send email notifications for batch creation
        """
        for user in users:
            try:
                user_prefs = UserNotificationPreference.objects.get(user=user)
                if not user_prefs.receive_email or not user_prefs.email_address:
                    continue
            except UserNotificationPreference.DoesNotExist:
                continue
            
            try:
                subject = f"New Batch Assigned: {batch.batch_number}"
                message = f"""
                Hello {user.get_full_name() or user.username},
                
                A new batch has been assigned to your factory:
                
                Batch Number: {batch.batch_number}
                Factory: {batch.factory.name}
                Wheat Amount: {batch.wheat_amount} tons
                Expected Output: {batch.expected_flour_output} tons
                Created: {batch.created_at.strftime('%Y-%m-%d %H:%M')}
                
                Please review and approve this batch when ready.
                
                Best regards,
                Mill Management System
                """
                
                # Send email
                success, error = self.email_service.send_email(
                    to_email=user_prefs.email_address,
                    subject=subject,
                    html_content=message,
                    user=user
                )
                
                if success:
                    logger.info(f"Sent batch creation email to {user.username}")
                else:
                    logger.error(f"Failed to send batch creation email to {user.username}: {error}")
                
            except Exception as e:
                logger.error(f"Error sending batch creation email to {user.username}: {str(e)}")
    
    def _send_batch_approved_emails(self, batch, users, approved_by):
        """
        Send email notifications for batch approval
        """
        for user in users:
            try:
                user_prefs = UserNotificationPreference.objects.get(user=user)
                if not user_prefs.receive_email or not user_prefs.email_address:
                    continue
            except UserNotificationPreference.DoesNotExist:
                continue
            
            try:
                subject = f"Batch Approved: {batch.batch_number}"
                message = f"""
                Hello {user.get_full_name() or user.username},
                
                A batch has been approved and is ready for production:
                
                Batch Number: {batch.batch_number}
                Factory: {batch.factory.name}
                Approved By: {approved_by.get_full_name() or approved_by.username}
                Approved At: {batch.approved_at.strftime('%Y-%m-%d %H:%M')}
                
                You can now start production for this batch.
                
                Best regards,
                Mill Management System
                """
                
                # Send email
                success, error = self.email_service.send_email(
                    to_email=user_prefs.email_address,
                    subject=subject,
                    html_content=message,
                    user=user
                )
                
                if success:
                    logger.info(f"Sent batch approval email to {user.username}")
                else:
                    logger.error(f"Failed to send batch approval email to {user.username}: {error}")
                
            except Exception as e:
                logger.error(f"Error sending batch approval email to {user.username}: {str(e)}")
    
    def _send_batch_started_emails(self, batch, users, started_by):
        """
        Send email notifications for batch start
        """
        for user in users:
            try:
                user_prefs = UserNotificationPreference.objects.get(user=user)
                if not user_prefs.receive_email or not user_prefs.email_address:
                    continue
            except UserNotificationPreference.DoesNotExist:
                continue
            
            try:
                subject = f"Production Started: {batch.batch_number}"
                message = f"""
                Hello {user.get_full_name() or user.username},
                
                Production has started for a batch:
                
                Batch Number: {batch.batch_number}
                Factory: {batch.factory.name}
                Started By: {started_by.get_full_name() or started_by.username}
                Started At: {timezone.now().strftime('%Y-%m-%d %H:%M')}
                
                Counter tracking is now active for this batch.
                
                Best regards,
                Mill Management System
                """
                
                # Send email
                success, error = self.email_service.send_email(
                    to_email=user_prefs.email_address,
                    subject=subject,
                    html_content=message,
                    user=user
                )
                
                if success:
                    logger.info(f"Sent batch start email to {user.username}")
                else:
                    logger.error(f"Failed to send batch start email to {user.username}: {error}")
                
            except Exception as e:
                logger.error(f"Error sending batch start email to {user.username}: {str(e)}")
    
    def _send_batch_completed_emails(self, batch, users, completed_by):
        """
        Send email notifications for batch completion
        """
        for user in users:
            try:
                user_prefs = UserNotificationPreference.objects.get(user=user)
                if not user_prefs.receive_email or not user_prefs.email_address:
                    continue
            except UserNotificationPreference.DoesNotExist:
                continue
            
            try:
                subject = f"Batch Completed: {batch.batch_number}"
                message = f"""
                Hello {user.get_full_name() or user.username},
                
                A batch has been completed:
                
                Batch Number: {batch.batch_number}
                Factory: {batch.factory.name}
                Completed By: {completed_by.get_full_name() or completed_by.username}
                Completed At: {timezone.now().strftime('%Y-%m-%d %H:%M')}
                
                Production has finished for this batch.
                
                Best regards,
                Mill Management System
                """
                
                # Send email
                success, error = self.email_service.send_email(
                    to_email=user_prefs.email_address,
                    subject=subject,
                    html_content=message,
                    user=user
                )
                
                if success:
                    logger.info(f"Sent batch completion email to {user.username}")
                else:
                    logger.error(f"Failed to send batch completion email to {user.username}: {error}")
                
            except Exception as e:
                logger.error(f"Error sending batch completion email to {user.username}: {str(e)}")
    
    def get_pending_batches_for_user(self, user):
        """
        Get batches that need approval from a specific user
        """
        try:
            # Get factories where user is responsible
            responsible_factories = user.responsible_factories.all()
            
            # Get pending batches for these factories
            pending_batches = Batch.objects.filter(
                factory__in=responsible_factories,
                status='pending'
            ).order_by('-created_at')
            
            return pending_batches
            
        except Exception as e:
            logger.error(f"Error getting pending batches for user {user.username}: {str(e)}")
            return Batch.objects.none()
    
    def get_approved_batches_for_user(self, user):
        """
        Get approved batches that can be started by a specific user
        """
        try:
            # Get factories where user is responsible
            responsible_factories = user.responsible_factories.all()
            
            # Get approved batches for these factories
            approved_batches = Batch.objects.filter(
                factory__in=responsible_factories,
                status='approved'
            ).order_by('-approved_at')
            
            return approved_batches
            
        except Exception as e:
            logger.error(f"Error getting approved batches for user {user.username}: {str(e)}")
            return Batch.objects.none() 