import React from 'react';
import { Marker, Circle, useMap } from 'react-leaflet';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import ReactDOMServer from 'react-dom/server';
import L from 'leaflet';
import { Button, Tooltip } from '@mui/material';
import Control from 'react-leaflet-custom-control';
import { useTranslation } from 'react-i18next';
import { buttonStyle, getLocationAwareStyles } from '../../../styles/buttonStyle';
import { useLocation } from '../context/LocationContext';

/**
 * Creates a custom Leaflet icon for displaying the user's location marker.
 * Renders a MyLocationIcon as an SVG string and converts it to a Leaflet divIcon.
 *
 * @returns {L.DivIcon} Leaflet divIcon representing the user's location
 */
const createLocationIcon = () => {
    const locationIconJSX = <MyLocationIcon sx={{ color: 'black', fontSize: 22 }} />;
    const svgLocationIcon = ReactDOMServer.renderToString(locationIconJSX);

    return L.divIcon({
        html: svgLocationIcon,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
        popupAnchor: [0, -11],
        className: 'location-icon',
    });
};

/**
 * Location control component that displays and manages the user's current location on the map.
 * Uses shared location context so all location-dependent buttons stay in sync.
 * Provides a button to re-center the map on the user's location.
 *
 * @returns {React.ReactElement} Location markers and control button
 */
const LocationControl = () => {
    const { t } = useTranslation();
    const { locationGranted, userPosition, requestGeolocation } = useLocation();
    const map = useMap();

    const flyToLocation = (location, mapInstance) => {
        const zoomLevel = Math.max(mapInstance.getZoom(), 16);
        mapInstance.flyTo(location, zoomLevel);
    };

    const handleFlyToLocationClick = () => {
        if (userPosition) {
            flyToLocation(userPosition, map);
        } else {
            requestGeolocation(position => flyToLocation(position, map));
        }
    };

    const { lat, lng } = userPosition || {};

    return (
        <>
            {userPosition && (
                <>
                    <Circle center={[lat, lng]} radius={userPosition.accuracy} />
                    <Marker position={userPosition} icon={createLocationIcon()} />
                </>
            )}
            <Control prepend position="bottomright">
                <Tooltip
                    title={
                        locationGranted ? t('centerOnMyLocation') : t('locationServicesDisabled')
                    }
                    placement="left"
                    arrow
                    enterTouchDelay={0}
                    leaveTouchDelay={1500}
                >
                    <Button
                        onClick={handleFlyToLocationClick}
                        variant="contained"
                        aria-label={t('centerButtonAriaLabel')}
                        sx={{
                            ...buttonStyle,
                            ...getLocationAwareStyles(locationGranted),
                        }}
                    >
                        <MyLocationIcon style={{ color: 'white', fontSize: 24 }} />
                    </Button>
                </Tooltip>
            </Control>
        </>
    );
};

export { LocationControl };
