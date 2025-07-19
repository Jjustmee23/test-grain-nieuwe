from django.core.management.base import BaseCommand
from mill.models import EmailTemplate

class Command(BaseCommand):
    help = 'Setup default email templates for welcome and password reset'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default email templates...')
        
        # Welcome Email Template
        welcome_template, created = EmailTemplate.objects.get_or_create(
            name='Welcome Email',
            template_type='welcome',
            defaults={
                'subject': 'Welcome to Mill Application, {{ username }}!',
                'html_content': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Welcome to Mill Application</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                        .button { display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
                        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🏭 Mill Application</h1>
                            <p>Welcome to our production management system</p>
                        </div>
                        <div class="content">
                            <h2>Welcome, {{ username }}!</h2>
                            <p>Thank you for joining the Mill Application. We're excited to have you on board!</p>
                            
                            <p>With your account, you can:</p>
                            <ul>
                                <li>Monitor factory production in real-time</li>
                                <li>Track batch progress and performance</li>
                                <li>Receive important notifications</li>
                                <li>Access detailed analytics and reports</li>
                                <li>Manage devices and factories</li>
                            </ul>
                            
                            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                            
                            <a href="http://yourdomain.com/login" class="button">Login to Your Account</a>
                        </div>
                        <div class="footer">
                            <p>This is an automated welcome message from the Mill Application system.</p>
                            <p>© {% now "Y" %} Mill Application. All rights reserved.</p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_content': '''
                Welcome to Mill Application, {{ username }}!
                
                Thank you for joining our production management system. We're excited to have you on board!
                
                With your account, you can:
                - Monitor factory production in real-time
                - Track batch progress and performance
                - Receive important notifications
                - Access detailed analytics and reports
                - Manage devices and factories
                
                If you have any questions or need assistance, please don't hesitate to contact our support team.
                
                Login to your account: http://yourdomain.com/login
                
                Best regards,
                The Mill Application Team
                ''',
                'variables': {
                    'username': 'User\'s username',
                    'first_name': 'User\'s first name',
                    'last_name': 'User\'s last name',
                    'email': 'User\'s email address'
                }
            }
        )
        
        if created:
            self.stdout.write('Created welcome email template')
        else:
            self.stdout.write('Welcome email template already exists')
        
        # Password Reset Template
        password_reset_template, created = EmailTemplate.objects.get_or_create(
            name='Password Reset',
            template_type='password_reset',
            defaults={
                'subject': 'Password Reset Request - Mill Application',
                'html_content': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Password Reset - Mill Application</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                        .button { display: inline-block; background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
                        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
                        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🔐 Password Reset</h1>
                            <p>Mill Application Security</p>
                        </div>
                        <div class="content">
                            <h2>Hello, {{ username }}!</h2>
                            <p>We received a request to reset your password for your Mill Application account.</p>
                            
                            <p>If you made this request, click the button below to reset your password:</p>
                            
                            <a href="{{ reset_link }}" class="button">Reset My Password</a>
                            
                            <div class="warning">
                                <strong>⚠️ Security Notice:</strong>
                                <ul>
                                    <li>This link will expire in 24 hours</li>
                                    <li>If you didn't request this reset, please ignore this email</li>
                                    <li>Never share this link with anyone</li>
                                </ul>
                            </div>
                            
                            <p>If the button doesn't work, copy and paste this link into your browser:</p>
                            <p style="word-break: break-all; background: #e9ecef; padding: 10px; border-radius: 5px;">{{ reset_link }}</p>
                            
                            <p>If you have any questions, please contact our support team.</p>
                        </div>
                        <div class="footer">
                            <p>This is an automated security message from the Mill Application system.</p>
                            <p>© {% now "Y" %} Mill Application. All rights reserved.</p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_content': '''
                Password Reset Request - Mill Application
                
                Hello, {{ username }}!
                
                We received a request to reset your password for your Mill Application account.
                
                If you made this request, click the link below to reset your password:
                {{ reset_link }}
                
                SECURITY NOTICE:
                - This link will expire in 24 hours
                - If you didn't request this reset, please ignore this email
                - Never share this link with anyone
                
                If you have any questions, please contact our support team.
                
                Best regards,
                The Mill Application Security Team
                ''',
                'variables': {
                    'username': 'User\'s username',
                    'reset_link': 'Password reset link',
                    'expires_at': 'Link expiration time'
                }
            }
        )
        
        if created:
            self.stdout.write('Created password reset template')
        else:
            self.stdout.write('Password reset template already exists')
        
        # System Alert Template
        system_alert_template, created = EmailTemplate.objects.get_or_create(
            name='System Alert',
            template_type='notification',
            defaults={
                'subject': 'System Alert - {{ alert_type }}',
                'html_content': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>System Alert - Mill Application</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #fd7e14 0%, #e55a00 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                        .alert-box { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
                        .footer { text-align: center; margin-top: 30px; color: #6c757d; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚨 System Alert</h1>
                            <p>Mill Application Notification</p>
                        </div>
                        <div class="content">
                            <h2>{{ alert_title }}</h2>
                            
                            <div class="alert-box">
                                <strong>Alert Type:</strong> {{ alert_type }}<br>
                                <strong>Severity:</strong> {{ severity }}<br>
                                <strong>Time:</strong> {{ timestamp }}
                            </div>
                            
                            <p>{{ message }}</p>
                            
                            {% if action_required %}
                            <p><strong>Action Required:</strong> {{ action_required }}</p>
                            {% endif %}
                            
                            <p>Please review this alert and take appropriate action if necessary.</p>
                        </div>
                        <div class="footer">
                            <p>This is an automated system alert from the Mill Application.</p>
                            <p>© {% now "Y" %} Mill Application. All rights reserved.</p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_content': '''
                System Alert - {{ alert_type }}
                
                {{ alert_title }}
                
                Alert Type: {{ alert_type }}
                Severity: {{ severity }}
                Time: {{ timestamp }}
                
                {{ message }}
                
                {% if action_required %}
                Action Required: {{ action_required }}
                {% endif %}
                
                Please review this alert and take appropriate action if necessary.
                
                Best regards,
                The Mill Application System
                ''',
                'variables': {
                    'alert_title': 'Title of the alert',
                    'alert_type': 'Type of alert (system, production, device)',
                    'severity': 'Alert severity (low, medium, high, critical)',
                    'timestamp': 'When the alert occurred',
                    'message': 'Detailed alert message',
                    'action_required': 'Required action (optional)'
                }
            }
        )
        
        if created:
            self.stdout.write('Created system alert template')
        else:
            self.stdout.write('System alert template already exists')
        
        self.stdout.write(
            self.style.SUCCESS('Email templates setup completed successfully!')
        )
        
        self.stdout.write('Created templates:')
        self.stdout.write('- Welcome Email Template')
        self.stdout.write('- Password Reset Template')
        self.stdout.write('- System Alert Template')
        
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Customize template content as needed')
        self.stdout.write('2. Test templates with real users')
        self.stdout.write('3. Configure Microsoft 365 settings for email delivery') 