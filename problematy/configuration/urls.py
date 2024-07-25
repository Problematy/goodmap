from django.urls import path
from configuration.views import AttributeListView, AttributeCreateView, AttributeUpdateView, AttributeDeleteView, \
    TypeOfPlaceListView, TypeOfPlaceCreateView, TypeOfPlaceUpdateView, TypeOfPlaceDeleteView, GeneralSettingsView, \
    get_attributes, get_values, get_attributes_for_type_of_place, AttributeValuesForPlaceView, \
    TypeOfPlaceAttributesView, get_attribute_values

urlpatterns = [
    #  Attributes
    path('attributes/', AttributeListView.as_view(), name='attribute_list'),
    path('attributes/create/', AttributeCreateView.as_view(), name='attribute_create'),
    path('attributes/<int:pk>/edit/', AttributeUpdateView.as_view(), name='attribute_edit'),
    path('attributes/<int:pk>/delete/', AttributeDeleteView.as_view(), name='attribute_delete'),



    #  Types of Places
    path('type_of_place/', TypeOfPlaceListView.as_view(), name='type_of_place_list'),
    path('type_of_place/create/', TypeOfPlaceCreateView.as_view(), name='type_of_place_create'),
    path('type_of_place/<int:pk>/edit/', TypeOfPlaceUpdateView.as_view(), name='type_of_place_edit'),
    path('type_of_place/<int:pk>/delete/', TypeOfPlaceDeleteView.as_view(), name='type_of_place_delete'),

    #  General Settings
    path('general_settings/', GeneralSettingsView.as_view(), name='general_settings'),

    #  Ajax
    path('attributes/get_values/<int:attribute_id>/', get_attribute_values, name='attribute-values'),
    path('attributes/get_attributes/', get_attributes, name='get_attributes'),
    path('attributes/get_values/<int:id>/', get_values, name='get_values'),
    path('attributes/values_for_place/<int:type_of_place_id>/<int:attribute_id>/',
         AttributeValuesForPlaceView.as_view(), name='attribute-values-for-place'),

    path('type_of_place/<int:pk>/attributes/', TypeOfPlaceAttributesView.as_view(), name='type_of_place_attributes'),
    path('get_attributes_for_type_of_place/<int:type_of_place_id>/', get_attributes_for_type_of_place,
         name='get-attributes-for-type'),
]
