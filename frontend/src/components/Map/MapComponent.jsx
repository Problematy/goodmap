import React, { useState } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import Control from 'react-leaflet-custom-control';
import { LocationControl } from './components/LocationControl';
import { SuggestNewPointButton } from './components/SuggestNewPointButton';
import { LocationPermissionBanner } from './components/LocationPermissionBanner';
import { mapConfig } from './map.config';
import { CustomZoomControl } from './components/ZoomControl';
import MapAutocomplete from './components/MapAutocomplete';
import ListViewButton from './components/ListView';
import AccessibilityTable from './components/AccessibilityTable';
import SaveMapConfiguration from './components/SaveMapConfiguration';
import { AppToaster } from '../common/AppToaster';
import { Markers } from './components/Markers';
import { MapLoadingOverlay } from './components/MapLoadingOverlay';
import { LocationProvider, useLocation } from './context/LocationContext';

/**
 * Inner map component that uses the shared location context.
 */
const MapComponentInner = () => {
    const { userPosition } = useLocation();
    const [isListViewOpen, setIsListViewOpen] = useState(false);
    const [isMapLoading, setIsMapLoading] = useState(true);

    const handleListViewButtonClick = () => {
        setIsListViewOpen(true);
    };

    const handleMapLoadingChange = isLoading => {
        setIsMapLoading(isLoading);
    };

    if (isListViewOpen) {
        return (
            <AccessibilityTable
                userPosition={userPosition}
                setIsAccessibilityTableOpen={setIsListViewOpen}
            />
        );
    }

    return (
        <div style={{ height: '100%', position: 'relative' }}>
            <AppToaster />
            <LocationPermissionBanner />
            <MapLoadingOverlay isLoading={isMapLoading} />
            <MapContainer
                center={mapConfig.initialMapCoordinates}
                zoom={mapConfig.initialMapZoom}
                scrollWheelZoom
                style={{ height: '100%' }}
                zoomControl={false}
            >
                <SaveMapConfiguration />
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&amp;copy <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
                    maxZoom={mapConfig.maxMapZoom}
                />
                {globalThis.FEATURE_FLAGS?.SHOW_SUGGEST_NEW_POINT_BUTTON && (
                    <Control position="bottomright" prepend>
                        <SuggestNewPointButton />
                    </Control>
                )}
                <Markers onLoadingChange={handleMapLoadingChange} />
                <LocationControl />
                <CustomZoomControl position="topright" />
                {globalThis.FEATURE_FLAGS?.SHOW_ACCESSIBILITY_TABLE && (
                    <ListViewButton onClick={handleListViewButtonClick} />
                )}
                {globalThis.FEATURE_FLAGS?.SHOW_SEARCH_BAR && <MapAutocomplete />}
            </MapContainer>
        </div>
    );
};

/**
 * Main map component that renders an interactive Leaflet map with various controls and features.
 * Wraps the map with LocationProvider for shared geolocation state.
 *
 * @returns {React.ReactElement} MapContainer with markers and controls, or AccessibilityTable when list view is active
 */
export const MapComponent = () => {
    return (
        <LocationProvider>
            <MapComponentInner />
        </LocationProvider>
    );
};
