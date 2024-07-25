from django import forms
from configuration.models import TypeOfPlace, Attribute


class TypeOfPlaceCreateForm(forms.ModelForm):
    attributes = forms.ModelMultipleChoiceField(
        queryset=Attribute.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    enable_website = forms.BooleanField(label='Enable Website Field', required=False)
    enable_comments = forms.BooleanField(label='Enable Comments Field', required=False)

    class Meta:
        model = TypeOfPlace
        fields = ['name', 'attributes', 'enable_website', 'enable_comments']

    def __init__(self, *args, **kwargs):
        super(TypeOfPlaceCreateForm, self).__init__(*args, **kwargs)
        self.fields['attributes'].widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data


class TypeOfPlaceEditForm(forms.ModelForm):
    attributes = forms.ModelMultipleChoiceField(
        queryset=Attribute.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    enable_website = forms.BooleanField(label='Enable Website Field', required=False)
    enable_comments = forms.BooleanField(label='Enable Comments Field', required=False)

    class Meta:
        model = TypeOfPlace
        fields = ['name', 'enable_website', 'enable_comments']

    def __init__(self, *args, **kwargs):
        super(TypeOfPlaceEditForm, self).__init__(*args, **kwargs)
        self.fields['attributes'].widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data
