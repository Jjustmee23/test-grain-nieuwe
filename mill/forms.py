from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from mill.models import Batch, Factory, ContactTicket, Feedback
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
    # Change to multiple city selection
    cities = forms.ModelMultipleChoiceField(
        queryset=City.objects.filter(status=True).order_by('name'),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    # Change to multiple factory selection
    factories = forms.ModelMultipleChoiceField(
        queryset=Factory.objects.none(),  # Will be populated dynamically
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Batch
        fields = ['batch_number', 'wheat_amount', 'waste_factor']
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initially, factory field should be empty
        self.fields['factories'].queryset = Factory.objects.none()

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

    def clean(self):
        cleaned_data = super().clean()
        cities = cleaned_data.get('cities')
        factories = cleaned_data.get('factories')
        
        if not cities:
            raise forms.ValidationError("Please select at least one city.")
        
        if not factories:
            raise forms.ValidationError("Please select at least one factory.")
        
        # Validate that factories belong to selected cities
        selected_city_ids = set(cities.values_list('id', flat=True))
        invalid_factories = []
        
        for factory in factories:
            if factory.city_id not in selected_city_ids:
                invalid_factories.append(factory.name)
        
        if invalid_factories:
            # Instead of raising an error, filter out invalid factories
            valid_factories = [f for f in factories if f.city_id in selected_city_ids]
            if valid_factories:
                cleaned_data['factories'] = valid_factories
                # Add a warning message
                from django.contrib import messages
                messages.warning(
                    None, 
                    f"Some factories were removed from selection as they don't belong to selected cities: {', '.join(invalid_factories)}"
                )
            else:
                raise forms.ValidationError("No valid factories found for the selected cities.")
        
        return cleaned_data

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

class FeedbackForm(forms.ModelForm):
    factories = forms.ModelMultipleChoiceField(
        queryset=Factory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Feedback
        fields = ['category', 'factories', 'all_factories', 'issue_date', 
                 'expected_value', 'shown_value', 'subject', 'message', 'priority']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        all_factories = cleaned_data.get('all_factories')
        factories = cleaned_data.get('factories')

        if not all_factories and not factories:
            raise forms.ValidationError(
                "Please either select specific factories or check 'All Factories'"
            )


class TicketResponseForm(forms.ModelForm):
    class Meta:
        model = TicketResponse
        fields = ['message']
        widgets = {
            'message': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': _('Type your response here...'),
                    'rows': 4
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].label = _('Your Response')
        self.fields['message'].help_text = _('Provide a detailed response to help resolve the issue')
