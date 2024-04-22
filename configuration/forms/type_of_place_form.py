from django import forms
from configuration.models import TypeOfPlace, Attribute


class TypeOfPlaceCreateForm(forms.ModelForm):
    attributes = forms.ModelMultipleChoiceField(
        queryset=Attribute.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    enable_website = forms.BooleanField(label='Enable Website Field', required=False)
    enable_comments = forms.BooleanField(label='Enable Comments Field', required=False)
    website = forms.URLField(required=False)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = TypeOfPlace
        fields = ['name', 'website', 'comments']

    def __init__(self, *args, **kwargs):
        super(TypeOfPlaceCreateForm, self).__init__(*args, **kwargs)
        self.fields['attributes'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['website'].required = False
        self.fields['comments'].required = False

    def clean(self):
        cleaned_data = super().clean()
        enable_website = cleaned_data.get('enable_website')
        enable_comments = cleaned_data.get('enable_comments')
        if not enable_website:
            cleaned_data['website'] = None
        if not enable_comments:
            cleaned_data['comments'] = None
        return cleaned_data


class TypeOfPlaceEditForm(forms.ModelForm):
    attributes = forms.ModelMultipleChoiceField(
        queryset=Attribute.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    enable_website = forms.BooleanField(label='Enable Website Field', required=False)
    enable_comments = forms.BooleanField(label='Enable Comments Field', required=False)
    website = forms.URLField(required=False)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = TypeOfPlace
        fields = ['name', 'website', 'comments']

    def __init__(self, *args, **kwargs):
        super(TypeOfPlaceEditForm, self).__init__(*args, **kwargs)
        self.fields['attributes'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['website'].required = False
        self.fields['comments'].required = False

    def clean(self):
        cleaned_data = super().clean()
        enable_website = cleaned_data.get('enable_website')
        enable_comments = cleaned_data.get('enable_comments')
        if not enable_website:
            cleaned_data['website'] = None
        if not enable_comments:
            cleaned_data['comments'] = None
        return cleaned_data
