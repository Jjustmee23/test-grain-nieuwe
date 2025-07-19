from django import forms
from models import Batch

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'factory', 'wheat_amount', 'waste_factor', 'start_date']
        widgets = {
            'start_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
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