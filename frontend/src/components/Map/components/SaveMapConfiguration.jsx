import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import { useMapStore } from '../store/map.store';

/**
 * Component that saves the current map configuration (zoom level) to the map store.
 * Listens to map movement events and updates the store whenever the map stops moving.
 * Note: Bounds calculation is prepared but not currently persisted (see commented fields below).
 * Automatically cleans up event listeners on unmount.
 *
 * @returns {null} This component doesn't render any UI elements
 */
const SaveMapConfiguration = () => {
    const map = useMap();

    useEffect(() => {
        const updateMapState = () => {
            const bounds = map.getBounds();
            const zoom = map.getZoom();

            useMapStore.getState().setMapConfiguration({
                // Will help in future with securing bounds
                // northWestBoundLat: bounds.getNorthWest().lat,
                // northWestBoundLng: bounds.getNorthWest().lng,
                // southEastBoundLat: bounds.getSouthEast().lat,
                // southEastBoundLng: bounds.getSouthEast().lng,
                zoom: zoom,
            });
        };

        updateMapState();
        map.on('moveend', updateMapState);

        return () => {
            map.off('moveend', updateMapState);
        };
    }, [map]);

    return null;
};

export default SaveMapConfiguration;
