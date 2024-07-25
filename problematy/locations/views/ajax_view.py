from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from configuration.models import TypeOfPlace, Value
from locations.models import Location


def get_attributes_for_type(request, type_of_place_id):
    type_of_place = get_object_or_404(TypeOfPlace, pk=type_of_place_id)
    attributes = type_of_place.attributes.values('id', 'name')
    return JsonResponse(list(attributes), safe=False)


def get_values_for_attribute(request, attribute_id):
    values = Value.objects.filter(attribute_id=attribute_id)
    values_data = list(values.values('id', 'content'))
    return JsonResponse(values_data, safe=False)


def get_selected_attributes_for_location(request, location_id):
    location = get_object_or_404(Location, pk=location_id)
    selected_attributes = location.location_attributes.all()

    attributes_data = [
        {
            'attribute_id': loc_attr.type_of_place_attribute.attribute.id,
            'type_of_place_id': loc_attr.type_of_place_attribute.type_of_place.id,
            'selected_values': list(loc_attr.selected_values.values_list('id', flat=True))
        }
        for loc_attr in selected_attributes
    ]
    return JsonResponse(attributes_data, safe=False)



