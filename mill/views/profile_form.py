from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.utils import timezone
from mill.models import UserProfile, UserNotificationPreference

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = UserProfile
        fields = ['team']
        widgets = {
            'team': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your team name'
            })
        }

class NotificationPreferenceForm(forms.ModelForm):
    """Form for notification preferences"""
    
    class Meta:
        model = UserNotificationPreference
        fields = ['receive_in_app', 'receive_email', 'email_address']
        widgets = {
            'receive_in_app': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'receive_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_address': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email for notifications'
            })
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['old_password'].widget.attrs.update({
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': 'Enter new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': 'Confirm new password'
        })