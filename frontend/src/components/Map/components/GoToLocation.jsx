import { useEffect, useState } from 'react';
import { useMap } from 'react-leaflet';
import { httpService } from '../../../services/http/httpService';
import { useMapStore } from '../store/map.store';

/**
 * Component that handles navigating to a specific location by ID.
 * Reads 'locationId' from URL query parameters, moves the map to that location
 * without animation, and opens the location's popup.
 *
 * @returns {null} This component renders nothing
 */
export const GoToLocation = () => {
    const map = useMap();
    const [hasNavigated, setHasNavigated] = useState(false);
    const setSelectedLocationId = useMapStore(state => state.setSelectedLocationId);

    useEffect(() => {
        if (hasNavigated) {
            return;
        }

        const urlParams = new URLSearchParams(globalThis.location.search);
        const locationId = urlParams.get('locationId');

        if (!locationId) {
            return;
        }

        const navigateToLocation = async () => {
            try {
                const location = await httpService.getLocation(locationId);

                if (!location?.position) {
                    console.warn('Location not found or has no position:', locationId);
                    return;
                }

                const [lat, lon] = location.position;
                map.setView([lat, lon], 16);
                setSelectedLocationId(locationId);
                setHasNavigated(true);
            } catch (error) {
                console.error('Failed to navigate to location:', error);
            }
        };

        navigateToLocation();
    }, [map, hasNavigated, setSelectedLocationId]);

    return null;
};
