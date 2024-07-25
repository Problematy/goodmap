from django.urls import path
from locations.views import LocationListView, LocationCreateView, LocationUpdateView, LocationDeleteView, \
    LocationHistoryView, get_attributes_for_type, get_selected_attributes_for_location, get_values_for_attribute, \
    download_locations

urlpatterns = [
    path('locations/', LocationListView.as_view(), name='location_list'),
    path('locations/create/', LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/edit/', LocationUpdateView.as_view(), name='location_edit'),
    path('locations/<int:pk>/delete/', LocationDeleteView.as_view(), name='location_delete'),
    path('locations/<int:pk>/history/', LocationHistoryView.as_view(), name='location_history'),
    #  JSON
    path('download-locations/', download_locations, name='download-locations'),
    #  Ajax
    path('type_of_place/<int:type_of_place_id>/attributes/', get_attributes_for_type, name='get_attributes_for_type'),
    path('attributes/<int:attribute_id>/values/', get_values_for_attribute, name='get_values_for_attribute'),
    path('locations/<int:location_id>/selected_attributes/', get_selected_attributes_for_location,
         name='get_selected_attributes_for_location'),
]
