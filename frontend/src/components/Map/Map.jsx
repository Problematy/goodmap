import ReactDOM from 'react-dom/client';
import React from 'react';
import { createPortal } from 'react-dom';
import FiltersForm from '../FiltersForm/FiltersForm';
import MapComponent from './MapComponent';
import { DeploymentDataProvider } from '../../context/DeploymentDataContext';
import { FiltersProvider } from '../../context/FiltersContext';
import AppToaster from '../common/AppToaster';

/**
 * Portals the map and filters form into DOM placeholders outside the React tree, under
 * DeploymentDataProvider (this deployment's fixed data, fetched once for every consumer) and
 * FiltersProvider (the one thing that changes as the app runs).
 *
 * Only #map is required: a deployment with no categories renders no left panel, so
 * #filter-form is legitimately absent and the filters portal is rendered only when there is
 * somewhere to put it.
 *
 * @returns {React.ReactElement|null} The portals, or null when #map is missing
 */
const MapWrap = () => {
    const mapPlaceholder = document.getElementById('map');
    const filtersPlaceholder = document.getElementById('filter-form');

    if (!mapPlaceholder) {
        console.error('Did not find a #map element to render the map into');
        return null;
    }

    return (
        <DeploymentDataProvider>
            <FiltersProvider>
                <AppToaster />
                {filtersPlaceholder && createPortal(<FiltersForm />, filtersPlaceholder)}
                {createPortal(<MapComponent />, mapPlaceholder)}
            </FiltersProvider>
        </DeploymentDataProvider>
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
