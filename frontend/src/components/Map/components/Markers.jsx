import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import httpService from '../../../services/http/httpService';
import MarkerPopup from '../../MarkerPopup/MarkerPopup';
import { useFilters } from '../../../context/FiltersContext';
import ClusterMarker from '../../MarkerPopup/ClusterMarker';

/**
 * Converts location data into marker components.
 * Supports both server-side clustering (ClusterMarker) and client-side clustering (MarkerPopup).
 * Behavior is controlled by FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING.
 *
 * @param {Array<Object>} locations - Array of location objects to render as markers
 * @returns {Array<React.ReactElement>} Array of marker components
 */
const getMarkers = locations => {
    if (globalThis.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING) {
        return locations.map(location => {
            if (location.type === 'cluster') {
                return <ClusterMarker cluster={location} key={location.cluster_uuid} />;
            }
            return <MarkerPopup place={location} key={location.uuid} />;
        });
    }
    // When server-side clustering is disabled, filter out any cluster objects
    // that the backend might still be sending, and only render actual locations
    return locations
        .filter(location => location.type !== 'cluster')
        .map(location => <MarkerPopup place={location} key={location.uuid} />);
};

/**
 * Component that fetches and renders map markers based on selected category filters.
 * Conditionally wraps markers in a MarkerClusterGroup for client-side clustering
 * when server-side clustering is disabled. With server-side clustering enabled,
 * markers and clusters are rendered directly.
 * Changes the map cursor to 'progress' while markers are loading.
 * Re-fetches markers whenever the selected categories change.
 *
 * @param {Object} props - Component props
 * @param {Function} [props.onLoadingChange] - Callback fired when loading state changes
 * @returns {React.ReactElement|Array} MarkerClusterGroup containing location markers, or empty array while loading
 */
const Markers = ({ onLoadingChange = null }) => {
    const { selectedFilters, isInitialized } = useFilters();
    const [markers, setMarkers] = useState([]);
    const [areMarkersLoaded, setAreMarkersLoaded] = useState(false);
    const map = useMap();
    useEffect(() => {
        // Wait until the initial filter state (including default-checked options)
        // is known, so the first locations fetch is already filtered.
        if (!isInitialized) {
            return undefined;
        }
        setAreMarkersLoaded(false);

        const fetchMarkers = async () => {
            let locations;
            try {
                locations = await httpService.getLocations(selectedFilters);
            } catch (error) {
                console.error('Failed to load locations:', error);
                setMarkers([]);
                setAreMarkersLoaded(true);
                return;
            }

            const markersToAdd = getMarkers(locations);

            const useServerSideClustering =
                globalThis.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING === true;

            // Only use client-side clustering when server-side clustering is disabled
            const markerCluster = useServerSideClustering ? (
                markersToAdd
            ) : (
                <MarkerClusterGroup
                    eventHandlers={{
                        add: () => {
                            setAreMarkersLoaded(true);
                        },
                    }}
                >
                    {markersToAdd}
                </MarkerClusterGroup>
            );

            setMarkers(markerCluster);

            // If using server-side clustering, mark as loaded immediately
            if (useServerSideClustering) {
                setAreMarkersLoaded(true);
            }
        };

        fetchMarkers();

        return () => {
            setMarkers([]);
        };
    }, [selectedFilters, isInitialized]);

    useEffect(() => {
        const mapContainer = map.getContainer();
        const cursorStyle = areMarkersLoaded ? 'auto' : 'progress';
        mapContainer.style.cursor = cursorStyle;

        return () => {
            mapContainer.style.cursor = 'auto';
        };
    }, [areMarkersLoaded, map]);

    useEffect(() => {
        if (onLoadingChange) {
            onLoadingChange(!areMarkersLoaded);
        }
    }, [areMarkersLoaded, onLoadingChange]);

    return markers;
};

Markers.propTypes = {
    onLoadingChange: PropTypes.func,
};

export default Markers;
