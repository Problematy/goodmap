from django import forms
from django.forms import ModelForm
from configuration.models import TypeOfPlaceAttribute, TypeOfPlace, Attribute
from locations.models import Location


class LocationCreateForm(ModelForm):
    type_of_place = forms.ModelChoiceField(
        queryset=TypeOfPlace.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=True,  # Now required
        empty_label='No Type of Place',
        error_messages={'required': 'This field is required'}
    )
    attributes = forms.ModelMultipleChoiceField(
        queryset=TypeOfPlaceAttribute.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    status = forms.ChoiceField(
        choices=[('visible', 'Visible'), ('hidden', 'Hidden')],
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )
    check_status = forms.ChoiceField(
        choices=[('exists', 'Exists'), ('does_not_exist', 'Does Not Exist'), ('check', 'To Check')],
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )
    website = forms.URLField(required=False)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Location
        fields = ['name', 'latitude', 'longitude', 'image', 'type_of_place', 'status', 'check_status', 'website', 'comments']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter location name', 'required': 'required'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        type_of_place_id = kwargs.pop('type_of_place_id', None)
        super(LocationCreateForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = True
        self.fields['latitude'].required = True
        self.fields['longitude'].required = True
        for field_name in ['name', 'latitude', 'longitude']:
            self.fields[field_name].error_messages = {'required': 'This field is required'}
        self.fields['status'].widget.attrs.update({'class': 'form-control select2'})
        self.fields['check_status'].widget.attrs.update({'class': 'form-control select2'})

        if type_of_place_id:
            attributes = Attribute.objects.filter(
                typeofplaceattribute__type_of_place_id=type_of_place_id
            ).distinct()
            self.fields['attributes'].queryset = attributes
            self.fields['attributes'].choices = [(attr.id, attr.name) for attr in attributes]


class LocationEditForm(forms.ModelForm):
    type_of_place = forms.ModelChoiceField(
        queryset=TypeOfPlace.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=True,  # Ensure consistency in field requirement as in CreateForm
        empty_label='No Type of Place',
        error_messages={'required': 'This field is required'}
    )
    attributes = forms.ModelMultipleChoiceField(
        queryset=TypeOfPlaceAttribute.objects.none(),  # Initially empty, will be set based on type_of_place
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    status = forms.ChoiceField(
        choices=[('visible', 'Visible'), ('hidden', 'Hidden')],
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )
    check_status = forms.ChoiceField(
        choices=[('exists', 'Exists'), ('does_not_exist', 'Does Not Exist'), ('check', 'To Check')],
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=False
    )

    class Meta:
        model = Location
        fields = ['name', 'latitude', 'longitude', 'image', 'type_of_place', 'status', 'check_status', 'website', 'comments']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter location name', 'required': 'required'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'style': 'height: 38px;'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super(LocationEditForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        type_of_place_id = instance.type_of_place.id if instance and instance.type_of_place else None

        # Set field requirements and error messages as in CreateForm
        self.fields['name'].required = True
        self.fields['latitude'].required = True
        self.fields['longitude'].required = True
        for field_name in ['name', 'latitude', 'longitude']:
            self.fields[field_name].error_messages = {'required': 'This field is required'}

        # Dynamically load and set initial values for attributes based on the type of place
        if type_of_place_id:
            attributes = Attribute.objects.filter(
                typeofplaceattribute__type_of_place_id=type_of_place_id
            ).distinct()
            self.fields['attributes'].queryset = attributes
            self.fields['attributes'].initial = [attr.id for attr in attributes]

        # Pre-populate other fields
        self.fields['status'].initial = instance.status if instance else 'visible'
        self.fields['check_status'].initial = instance.check_status if instance else 'check'
