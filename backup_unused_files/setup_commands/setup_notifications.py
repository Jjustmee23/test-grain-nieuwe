from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mill.models import (
    NotificationCategory, UserNotificationPreference, 
    EmailTemplate, Microsoft365Settings
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup notification system with default categories and user preferences'

    def handle(self, *args, **options):
        self.stdout.write('Setting up notification system...')
        
        # Create default notification categories
        categories_data = [
            {
                'name': 'Batch Assignment',
                'description': 'Notifications about batch assignments and updates',
                'notification_type': 'batch_assignment',
                'requires_admin': False,
                'requires_super_admin': False
            },
            {
                'name': 'Batch Approval',
                'description': 'Notifications about batch approval requests and decisions',
                'notification_type': 'batch_approval',
                'requires_admin': True,
                'requires_super_admin': False
            },
            {
                'name': 'Batch Rejection',
                'description': 'Notifications about batch rejections and reasons',
                'notification_type': 'batch_rejection',
                'requires_admin': True,
                'requires_super_admin': False
            },
            {
                'name': 'Batch Completion',
                'description': 'Notifications about batch completion and results',
                'notification_type': 'batch_completion',
                'requires_admin': False,
                'requires_super_admin': False
            },
            {
                'name': 'System Warning',
                'description': 'System warnings and alerts',
                'notification_type': 'system_warning',
                'requires_admin': False,
                'requires_super_admin': False
            },
            {
                'name': 'Device Alert',
                'description': 'Device status alerts and issues',
                'notification_type': 'device_alert',
                'requires_admin': True,
                'requires_super_admin': False
            },
            {
                'name': 'Production Alert',
                'description': 'Production-related alerts and notifications',
                'notification_type': 'production_alert',
                'requires_admin': True,
                'requires_super_admin': False
            },
            {
                'name': 'Maintenance Reminder',
                'description': 'Maintenance reminders and schedules',
                'notification_type': 'maintenance_reminder',
                'requires_admin': True,
                'requires_super_admin': False
            },
            {
                'name': 'User Management',
                'description': 'User account management notifications',
                'notification_type': 'user_management',
                'requires_admin': False,
                'requires_super_admin': True
            },
            {
                'name': 'Data Export',
                'description': 'Data export completion notifications',
                'notification_type': 'data_export',
                'requires_admin': False,
                'requires_super_admin': False
            },
            {
                'name': 'Factory Status',
                'description': 'Factory status updates and alerts',
                'notification_type': 'factory_status',
                'requires_admin': True,
                'requires_super_admin': False
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = NotificationCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
            created_categories.append(category)
        
        # Create default email templates
        templates_data = [
            {
                'name': 'Batch Assignment Template',
                'subject': '[Mill App] New Batch Assignment: {{ batch.batch_number }}',
                'html_content': '''
                <h2>New Batch Assignment</h2>
                <p>You have been assigned to batch <strong>{{ batch.batch_number }}</strong> at {{ batch.factory.name }}.</p>
                <p><strong>Start Date:</strong> {{ batch.start_date|date:"F j, Y" }}</p>
                <p><strong>Expected Duration:</strong> {{ batch.expected_duration }} hours</p>
                <p>Please review the batch details and begin processing.</p>
                ''',
                'text_content': '''
                New Batch Assignment
                
                You have been assigned to batch {{ batch.batch_number }} at {{ batch.factory.name }}.
                Start Date: {{ batch.start_date|date:"F j, Y" }}
                Expected Duration: {{ batch.expected_duration }} hours
                
                Please review the batch details and begin processing.
                ''',
                'category_name': 'Batch Assignment'
            },
            {
                'name': 'Batch Approval Template',
                'subject': '[Mill App] Batch Approval Required: {{ batch.batch_number }}',
                'html_content': '''
                <h2>Batch Approval Required</h2>
                <p>A new batch <strong>{{ batch.batch_number }}</strong> requires your approval.</p>
                <p><strong>Factory:</strong> {{ batch.factory.name }}</p>
                <p><strong>Created by:</strong> {{ batch.created_by.username }}</p>
                <p><strong>Start Date:</strong> {{ batch.start_date|date:"F j, Y" }}</p>
                <p>Please review and approve or reject this batch.</p>
                ''',
                'text_content': '''
                Batch Approval Required
                
                A new batch {{ batch.batch_number }} requires your approval.
                Factory: {{ batch.factory.name }}
                Created by: {{ batch.created_by.username }}
                Start Date: {{ batch.start_date|date:"F j, Y" }}
                
                Please review and approve or reject this batch.
                ''',
                'category_name': 'Batch Approval'
            },
            {
                'name': 'System Warning Template',
                'subject': '[Mill App] System Warning: {{ notification.title }}',
                'html_content': '''
                <h2>System Warning</h2>
                <p><strong>{{ notification.title }}</strong></p>
                <p>{{ notification.message }}</p>
                <p>Please take appropriate action to resolve this issue.</p>
                ''',
                'text_content': '''
                System Warning
                
                {{ notification.title }}
                {{ notification.message }}
                
                Please take appropriate action to resolve this issue.
                ''',
                'category_name': 'System Warning'
            }
        ]
        
        for template_data in templates_data:
            category_name = template_data.pop('category_name')
            try:
                category = NotificationCategory.objects.get(name=category_name)
                template, created = EmailTemplate.objects.get_or_create(
                    name=template_data['name'],
                    category=category,
                    defaults=template_data
                )
                if created:
                    self.stdout.write(f'Created template: {template.name}')
                else:
                    self.stdout.write(f'Template already exists: {template.name}')
            except NotificationCategory.DoesNotExist:
                self.stdout.write(f'Category not found: {category_name}')
        
        # Setup user preferences for existing users
        users = User.objects.filter(is_active=True)
        for user in users:
            preferences, created = UserNotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'receive_in_app': True,
                    'receive_email': bool(user.email),
                    'email_address': user.email
                }
            )
            
            if created:
                # Set default categories based on user role
                if user.is_superuser:
                    # Super admins get all categories
                    preferences.enabled_categories.set(created_categories)
                    preferences.is_super_admin = True
                elif user.groups.filter(name='admin').exists():
                    # Admins get admin categories and below
                    admin_categories = [cat for cat in created_categories 
                                      if not cat.requires_super_admin]
                    preferences.enabled_categories.set(admin_categories)
                    preferences.is_admin = True
                else:
                    # Regular users get basic categories
                    basic_categories = [cat for cat in created_categories 
                                      if not cat.requires_admin and not cat.requires_super_admin]
                    preferences.enabled_categories.set(basic_categories)
                
                preferences.save()
                self.stdout.write(f'Created preferences for user: {user.username}')
            else:
                self.stdout.write(f'Preferences already exist for user: {user.username}')
        
        # Create default Microsoft 365 settings (inactive)
        ms365_settings, created = Microsoft365Settings.objects.get_or_create(
            is_active=False,
            defaults={
                'client_id': '',
                'client_secret': '',
                'tenant_id': '',
                'redirect_uri': '',
                'from_email': '',
                'from_name': 'Mill Application',
                'smtp_server': 'smtp.office365.com',
                'smtp_port': 587,
                'use_tls': True
            }
        )
        
        if created:
            self.stdout.write('Created default Microsoft 365 settings (inactive)')
        else:
            self.stdout.write('Microsoft 365 settings already exist')
        
        self.stdout.write(
            self.style.SUCCESS('Notification system setup completed successfully!')
        )
        
        self.stdout.write(f'Created {len(created_categories)} notification categories')
        self.stdout.write(f'Setup preferences for {users.count()} users')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Configure Microsoft 365 OAuth2 settings in the admin panel')
        self.stdout.write('2. Test email connection')
        self.stdout.write('3. Customize notification preferences for users') 