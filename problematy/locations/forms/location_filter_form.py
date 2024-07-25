from django import forms
from locations.models import Location
from configuration.models import TypeOfPlace, Attribute, TypeOfPlaceAttribute, Value


class LocationFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'})
    )
    status = forms.ChoiceField(
        choices=[('', 'No Status')] + Location.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    check_status = forms.ChoiceField(
        choices=[('', 'No Check Status')] + Location.CHECK_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    type_of_place = forms.ModelChoiceField(
        queryset=TypeOfPlace.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        empty_label='No Type of Place'
    )
    attribute = forms.ModelChoiceField(
        queryset=Attribute.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select2', 'id': 'id_attribute'}),
        label='Attribute',
        empty_label='No Attributes'
    )

    attribute_value = forms.ModelMultipleChoiceField(
        queryset=Value.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2 attribute-value-selector',
            'data-placeholder': 'Select values'
        }),
        label='Attribute Value'
    )

    def __init__(self, *args, **kwargs):
        super(LocationFilterForm, self).__init__(*args, **kwargs)
        self.fields['attribute'].queryset = Attribute.objects.none()
        if 'type_of_place' in self.data:
            try:
                type_id = int(self.data.get('type_of_place'))
                self.fields['attribute'].queryset = Attribute.objects.filter(
                    typeofplaceattribute__type_of_place_id=type_id).distinct()
                if 'attribute' in self.data:
                    attr_id = int(self.data.get('attribute'))
                    self.fields['attribute_value'].queryset = Value.objects.filter(
                        attribute_id=attr_id,
                        attribute__typeofplaceattribute__type_of_place_id=type_id
                    ).distinct()
            except (ValueError, TypeError):
                pass
