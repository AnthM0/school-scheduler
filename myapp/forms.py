from django import forms
from .models import Class
from datetime import time

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'day', 'start_time', 'end_time']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Math, English...',
                'class': 'modal-input',
            }),
            'day': forms.Select(attrs={
                'class': 'modal-input',
            }),
            'start_time': forms.Select(attrs={
                'class': 'modal-input',
            }),
            'end_time': forms.Select(attrs={
                'class': 'modal-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].widget = forms.Select(
            choices=self._time_choices(),
            attrs={'class': 'modal-input'}
        )
        self.fields['end_time'].widget = forms.Select(
            choices=self._time_choices(),
            attrs={'class': 'modal-input'}
        )

    def _time_choices(self):
        from datetime import datetime, timedelta
        choices = []
        start = datetime.strptime('7:30 AM', '%I:%M %p')
        end = datetime.strptime('4:30 PM', '%I:%M %p')
        current = start
        while current <= end:
            value = current.strftime('%H:%M')
            label = current.strftime('%I:%M %p').lstrip('0')
            choices.append((value, label))
            current += timedelta(minutes=30)
        return choices

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError('End time must be after start time.')
            if start_time < time(7, 30):
                raise forms.ValidationError('Start time cannot be before 7:30 AM.')
            if end_time > time(16, 30):
                raise forms.ValidationError('End time cannot be after 4:30 PM.')

        return cleaned_data