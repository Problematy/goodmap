import ReactDOM from 'react-dom/client';
import React from 'react';

import { Marker, Popup } from 'react-leaflet';

import { httpService } from '../../services/http/httpService';
import { FiltersForm } from '../FiltersForm/FiltersForm';
import { MarkerPopup } from '../MarkerPopup/MarkerPopup';
import { MapComponent } from './MapComponent';

const mapPlaceholder = ReactDOM.createRoot(document.getElementById('map'));
const filtersPlaceholder = ReactDOM.createRoot(document.getElementById('filter-form'));

function getSelectedCheckboxesOfCategory(filterType) {
    const checkedBoxesTypes = document.querySelectorAll(`.filter.${filterType}:checked`);
    const types = Array.from(checkedBoxesTypes)
        .map(checkboxNode => `${filterType}=${checkboxNode.value}`)
        .join('&');

    return types;
}

export async function getNewMarkers(categories) {
    const allCheckboxes = categories.map(([categoryString]) =>
        getSelectedCheckboxesOfCategory(categoryString),
    );
    const filtersUrlQueryString = allCheckboxes.filter(n => n).join('&');
    const locations = await httpService.getLocations(filtersUrlQueryString);
    return locations.map(location => (
        <Marker position={location.position} key={location.metadata.UUID}>
            <Popup>
                <MarkerPopup place={location} />
            </Popup>
        </Marker>
    ));
}

export async function repaintMarkers(categories) {
    try {
        const newMarkers = await getNewMarkers(categories);
        const mainMap = <MapComponent markers={newMarkers} />;
        mapPlaceholder.render(mainMap);
    } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Error repainting markers:', error);
    }
}

export const Map = async () => {
    httpService.getCategoriesData().then(categoriesData => {
        const parsedCategoriesData = categoriesData.map(categoryData => categoryData[0]);

        repaintMarkers(parsedCategoriesData);
        filtersPlaceholder.render(
            <FiltersForm
                categoriesData={categoriesData}
                onClick={() => repaintMarkers(parsedCategoriesData)}
            />,
        );
    });
};
