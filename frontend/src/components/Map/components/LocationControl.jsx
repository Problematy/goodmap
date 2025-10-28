import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Marker, Circle, useMap } from 'react-leaflet';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import ReactDOMServer from 'react-dom/server';
import L from 'leaflet';
import { Snackbar, Button } from '@mui/material';
import Control from 'react-leaflet-custom-control';
import { useTranslation } from 'react-i18next';
import { buttonStyle } from '../../../styles/buttonStyle';

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
 * Automatically requests geolocation on mount and displays a marker with accuracy circle.
 * Provides a button to re-center the map on the user's location.
 * Shows a snackbar notification if location services are denied or unavailable.
 *
 * @param {Object} props - Component props
 * @param {Function} props.setUserPosition - Callback function to update user position in parent component
 * @returns {React.ReactElement} Location markers and control button, or null if no position available
 */
const LocationControl = ({ setUserPosition: setUserPositionProp }) => {
    const { t } = useTranslation();
    const [userPosition, setUserPosition] = useState(null);
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const map = useMap();

    const flyToLocation = (location, mapInstance) => {
        const zoomLevel = Math.max(mapInstance.getZoom(), 16);
        mapInstance.flyTo(location, zoomLevel);
    };

    const handleLocationFound = useCallback(
        e => {
            const position = { ...e.latlng, accuracy: e.accuracy };
            setUserPosition(position);
            setUserPositionProp(position);
        },
        [setUserPositionProp],
    );

    const handleLocationError = useCallback(
        e => {
            if (e.code === 1) {
                // User denied Geolocation
                setSnackbarOpen(true);
                setUserPosition(null);
            }
        },
        [map],
    );

    const handleSnackbarClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }
        setSnackbarOpen(false);
    };

    const handleFlyToLocationClick = () => {
        if (userPosition) {
            flyToLocation(userPosition, map);
        }
    };

    useEffect(() => {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    const accuracy = position.coords.accuracy;
                    // Ensure accuracy is a valid number, default to 50 meters if not
                    const validAccuracy =
                        !Number.isNaN(Number(accuracy)) && accuracy != null ? Number(accuracy) : 50;
                    handleLocationFound({ latlng: { lat, lng }, accuracy: validAccuracy });
                },
                () => {
                    handleLocationError({ code: 1 });
                },
            );
        } else {
            handleLocationError({ code: 1 });
        }
    }, [handleLocationFound, handleLocationError]);

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
                <Button
                    onClick={handleFlyToLocationClick}
                    style={buttonStyle}
                    variant="contained"
                    aria-label={t('centerButtonAriaLabel')}
                >
                    <MyLocationIcon style={{ color: 'white', fontSize: 24 }} />
                </Button>

                <Snackbar
                    open={snackbarOpen}
                    autoHideDuration={4000}
                    onClose={handleSnackbarClose}
                    message={t('locationServicesDisabled')}
                />
            </Control>
        </>
    );
};

LocationControl.propTypes = {
    setUserPosition: PropTypes.func.isRequired,
};

export { LocationControl };
