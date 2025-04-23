from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from mill.models import Batch, Factory, ContactTicket
from django.utils.translation import gettext_lazy as _



class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class FactoryForm(forms.ModelForm):
    class Meta:
        model = Factory
        fields = ['name', 'city', 'status']
class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'factory', 'wheat_amount', 'waste_factor']
        widgets = {
            'waste_factor': forms.NumberInput(
                attrs={
                    'min': '0',
                    'max': '100',
                    'step': '0.1',
                    'class': 'form-control'
                }
            ),
            'wheat_amount': forms.NumberInput(
                attrs={
                    'min': '0',
                    'step': '0.01',
                    'class': 'form-control'
                }
            ),
            'batch_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter Batch Number'
                }
            ),
            'factory': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            )
        }


    def clean_batch_number(self):
        batch_number = self.cleaned_data.get('batch_number')
        if Batch.objects.filter(batch_number=batch_number).exists():
            raise forms.ValidationError("This batch number already exists.")
        return batch_number

    def clean_waste_factor(self):
        waste_factor = self.cleaned_data.get('waste_factor')
        if waste_factor < 0 or waste_factor > 100:
            raise forms.ValidationError("Waste factor must be between 0 and 100.")
        return waste_factor

class ContactTicketForm(forms.ModelForm):
    class Meta:
        model = ContactTicket
        fields = [
            'name', 
            'email', 
            'phone', 
            'ticket_type', 
            'subject', 
            'message', 
            'priority', 
            'factory'
        ]
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Your Name')
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Your Email')
                }
            ),
            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Your Phone Number (Optional)')
                }
            ),
            'ticket_type': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
            'subject': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Subject')
                }
            ),
            'message': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Your Message'),
                    'rows': 5
                }
            ),
            'priority': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
            'factory': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields optional
        self.fields['phone'].required = False
        self.fields['factory'].required = False
        
        # Add help text
        self.fields['phone'].help_text = _('Optional - Enter your phone number for urgent matters')
        self.fields['priority'].help_text = _('Select the urgency level of your ticket')
        
        # Update choice fields labels
        self.fields['ticket_type'].label = _('Type of Issue')
        self.fields['priority'].label = _('Urgency Level')
        
        # Filter active factories only if there are any
        if 'factory' in self.fields:
            self.fields['factory'].queryset = Factory.objects.filter(status=True)