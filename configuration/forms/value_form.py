from django import forms
from configuration.models import Value


class ValueForm(forms.ModelForm):
    class Meta:
        model = Value
        fields = ['content']

    def __init__(self, *args, **kwargs):
        super(ValueForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'form-control'})
