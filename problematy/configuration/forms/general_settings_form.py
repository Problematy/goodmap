# В вашем файле forms.py
from django import forms
from django.core.exceptions import ValidationError
from configuration.models import GeneralSetting

class GeneralSettingForm(forms.ModelForm):
    checking_period = forms.IntegerField(
        min_value=1,
        max_value=500,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter number of days'
        }),
        label="Places checking period (1 to 500 days)"
    )

    class Meta:
        model = GeneralSetting
        fields = ['checking_period']

    def clean_checking_period(self):
        checking_period = self.cleaned_data.get("checking_period")
        if not 1 <= checking_period <= 500:
            raise ValidationError("Please enter a value between 1 and 500.")
        return checking_period
