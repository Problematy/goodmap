import * as ReactDOMServer from 'react-dom/server';
import ReactDOM from 'react-dom/client';
import React from 'react';
import Leaflet from 'leaflet';
import 'leaflet.markercluster';

import { httpService } from '../../services/http/httpService';
import { FiltersForm } from '../FiltersForm/FiltersForm';
import { MarkerPopup } from '../MarkerPopup/MarkerPopup';
import { createBaseMap } from './createBaseMap';

let markers = Leaflet.markerClusterGroup();
let mainMap = null;

function onLocationFound(e, _map, locationMarker, circleMarker) {
    const radius = e.accuracy / 2;
    locationMarker.setLatLng(e.latlng);
    circleMarker.setLatLng(e.latlng).setRadius(radius);
}

function getSelectedCheckboxesOfCategory(filterType) {
    const checkedBoxesTypes = document.querySelectorAll(`.filter.${filterType}:checked`);
    const types = Array.from(checkedBoxesTypes)
        .map(checkboxNode => `${filterType}=${checkboxNode.value}`)
        .join('&');

    return types;
}

function getNewMarkers(categories) {
    const markersCluster = Leaflet.markerClusterGroup();
    const allCheckboxes = categories.map(([categoryString]) =>
        getSelectedCheckboxesOfCategory(categoryString),
    );
    const filtersUrlQueryString = allCheckboxes.filter(n => n).join('&');

    httpService
        .getLocations(filtersUrlQueryString)
        .then(response => {
            response.map(x =>
                Leaflet.marker(x.position)
                    .addTo(markersCluster)
                    .bindPopup(ReactDOMServer.renderToStaticMarkup(<MarkerPopup place={x} />)),
            );
        })
        .catch(error => console.error(error));

    return markersCluster;
}

export const repaintMarkers = categories => {
    mainMap.removeLayer(markers);
    markers = getNewMarkers(categories);
    mainMap.addLayer(markers);
};

export const Map = async () => {
    const categories = await httpService.getCategories();
    mainMap = createBaseMap(onLocationFound);

    mainMap.addLayer(markers);
    getNewMarkers(categories);

    httpService.getCategoriesData().then(categoriesData => {
        const parsedCategoriesData = categoriesData.map(categoryData => categoryData[0]);
        const filtersPlaceholder = ReactDOM.createRoot(document.getElementById('filter-form'));

        repaintMarkers(parsedCategoriesData);
        filtersPlaceholder.render(
            <FiltersForm
                categoriesData={categoriesData}
                onClick={() => repaintMarkers(parsedCategoriesData)}
            />,
        );
    });
};
