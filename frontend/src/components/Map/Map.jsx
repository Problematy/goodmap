import ReactDOM from 'react-dom/client';
import React from 'react';
import { createPortal } from 'react-dom';
import FiltersForm from '../FiltersForm/FiltersForm';
import MapComponent from './MapComponent';
import { CategoriesProvider } from '../Categories/CategoriesContext';
import AppToaster from '../common/AppToaster';

/**
 * Wrapper component that renders the map and filters form into their respective DOM placeholders.
 * Uses React portals to render components into pre-existing DOM elements outside the React tree.
 * Wraps both components with CategoriesProvider for shared filter state management.
 *
 * @returns {React.ReactElement|null} Portals for FiltersForm and MapComponent, or null if placeholders not found
 */
const MapWrap = () => {
    const mapPlaceholder = document.getElementById('map');
    const filtersPlaceholder = document.getElementById('filter-form');

    if (!filtersPlaceholder || !mapPlaceholder) {
        console.error('Did not find any DOM elements to render the map or filters form');
        return null;
    }

    return (
        <CategoriesProvider>
            <AppToaster />
            {createPortal(<FiltersForm />, filtersPlaceholder)}
            {createPortal(<MapComponent />, mapPlaceholder)}
        </CategoriesProvider>
    );
};

/**
 * Main entry point for the map application.
 * Creates a root DOM element, initializes React rendering, and mounts the MapWrap component.
 * This function is typically called once during application initialization.
 *
 * @returns {void}
 */
const MapContainer = () => {
    const appContainer = document.createElement('div');
    document.body.appendChild(appContainer);

    const root = ReactDOM.createRoot(appContainer);
    root.render(<MapWrap />);
};

export default MapContainer;
