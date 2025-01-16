import ReactDOM from 'react-dom/client';
import React, { useEffect } from 'react';
import { httpService } from '../../services/http/httpService';
import { FiltersForm } from '../FiltersForm/FiltersForm';
import { MapComponent } from './MapComponent';
import { useMapStore } from './store/map.store';
import { CategoriesProvider } from '../Categories/CategoriesContext';
import { createPortal } from 'react-dom';
import useDebounce from '../../utils/hooks/useDebounce';

const MapWrap = () => {
    const mapPlaceholder = document.getElementById('map');
    const filtersPlaceholder = document.getElementById('filter-form');

    if (!filtersPlaceholder || !mapPlaceholder) {
        console.error('Did not find any DOM elements to render the map or filters form');
        return null;
    }

    return (
        <CategoriesProvider>
            {createPortal(<FiltersForm />, filtersPlaceholder)}
            {createPortal(<MapComponent />, mapPlaceholder)}
        </CategoriesProvider>
    );
};

export const MapContainer = () => {
    const appContainer = document.createElement('div');
    document.body.appendChild(appContainer);

    const root = ReactDOM.createRoot(appContainer);
    root.render(<MapWrap />);
};
