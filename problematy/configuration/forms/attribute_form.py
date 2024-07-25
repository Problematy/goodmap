from django import forms
from configuration.models import Attribute, Value
from django.db import transaction


class AttributeForm(forms.ModelForm):
    values = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Enter values separated by commas'
        }),
        required=False
    )
    class Meta:
        model = Attribute
        fields = ['name', 'values', 'visible_in_categories', 'visible_in_visible_data']

    def __init__(self, *args, **kwargs):
        super(AttributeForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            initial_values = self.instance.get_values_list()
            self.fields['values'].initial = ", ".join(initial_values)

    def clean_values(self):
        values = self.cleaned_data.get('values', '')
        if isinstance(values, list):
            return values  # или обработать список по вашему усмотрению
        return [v.strip() for v in values.split(',') if v.strip()]

    def save_values(self, instance):
        current_values = self.cleaned_data['values']

        if isinstance(current_values, str):
            current_values = [value.strip() for value in current_values.split(',') if value.strip()]

        existing_values = list(instance.values.values_list('content', flat=True))
        for value in current_values:
            if value and value not in existing_values:
                Value.objects.create(attribute=instance, content=value)
        # Удаляем неиспользуемые значения
        instance.values.exclude(content__in=current_values).delete()

    def save_values(self, instance):
        if self.cleaned_data['values']:
            current_values = [value.strip() for value in self.cleaned_data['values'].split(',')]
            existing_values = list(instance.values.values_list('content', flat=True))
            for value in current_values:
                if value and value not in existing_values:
                    Value.objects.create(attribute=instance, content=value)
            instance.values.exclude(content__in=current_values).delete()
