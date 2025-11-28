from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['region', 'latitude', 'longitude', 'status', 'description', 'photo']
        widgets = {
            'region': forms.Select(attrs={
                'id': 'region',
                'class': 'form-control'
            }),
            'latitude': forms.TextInput(attrs={
                'id': 'latitude',
                'placeholder': 'Latitude',
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'longitude': forms.TextInput(attrs={
                'id': 'longitude',
                'placeholder': 'Longitude',
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'status': forms.Select(attrs={
                'id': 'status',
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'id': 'desc',
                'placeholder': '120 characters only',
                'maxlength': '120',
                'class': 'form-control'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'required': 'required'
            })
        }
        labels = {
            'region': 'Choose region:',
            'latitude': 'Latitude *',
            'longitude': 'Longitude *',
            'status': 'Input status:',
            'description': 'Description (Optional)',
            'photo': 'Upload Photo *'
        }