import ReactDOM from 'react-dom/client';
import React from 'react';
import { httpService } from '../../services/http/httpService';
import { FiltersForm } from '../FiltersForm/FiltersForm';
import { MarkerPopup } from '../MarkerPopup/MarkerPopup';
import { MapComponent } from './MapComponent';

const mapPlaceholder = document.getElementById('map')
    ? ReactDOM.createRoot(document.getElementById('map'))
    : null;
const filtersPlaceholder = document.getElementById('filter-form')
    ? ReactDOM.createRoot(document.getElementById('filter-form'))
    : null;

export function getSelectedCheckboxesOfCategory(filterType) {
    const checkedBoxesTypes = document.querySelectorAll(`.filter.${filterType}:checked`);
    const types = Array.from(checkedBoxesTypes)
        .map(checkboxNode => `${filterType}=${checkboxNode.value}`)
        .join('&');

    return types;
}

export async function getNewMarkers(categories, allCheckboxes) {
    const filtersUrlQueryString = allCheckboxes.filter(n => n).join('&');
    const locations = await httpService.getLocations(filtersUrlQueryString);

    let markers = locations.map(location => {
        const locationKey =
            window.USE_LAZY_LOADING ?? false ? location.uuid : location.metadata.uuid;
        return <MarkerPopup place={location} key={locationKey} />;
    });
    return markers;
}

export async function repaintMarkers(categories) {
    try {
        const allCheckboxes = categories.map(([categoryString]) =>
            getSelectedCheckboxesOfCategory(categoryString),
        );
        const newMarkers = await getNewMarkers(categories, allCheckboxes);

        const mainMap = <MapComponent markers={newMarkers} allCheckboxes={allCheckboxes} />;
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
