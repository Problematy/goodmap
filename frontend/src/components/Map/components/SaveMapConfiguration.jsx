import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import { useMapStore } from '../store/map.store';

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
};

export default SaveMapConfiguration;
