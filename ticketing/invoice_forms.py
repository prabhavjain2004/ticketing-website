from django import forms
from .models import EventCommission, Event

class EventCommissionForm(forms.ModelForm):
    """Form for creating/updating event commission settings"""
    class Meta:
        model = EventCommission
        fields = ['commission_type', 'commission_value']
        widgets = {
            'commission_type': forms.Select(attrs={'class': 'form-control'}),
            'commission_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class EventFilterForm(forms.Form):
    """Form for filtering invoices by event, date range, etc."""
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        required=False,
        empty_label="All Events",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Start Date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'End Date'
        })
    )
