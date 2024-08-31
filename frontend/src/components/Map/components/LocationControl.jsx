import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Marker, CircleMarker, useMap } from 'react-leaflet';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import ReactDOMServer from 'react-dom/server';
import L from 'leaflet';
import { Snackbar } from '@mui/material';

import { LocationButton } from './LocationButton';

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

const LocationControl = ({ setUserPosition: setUserPositionProp }) => {
    const [userPosition, setUserPosition] = useState(null);
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const map = useMap();

    const handleLocationFound = e => {
        setUserPosition(e.latlng);
        setUserPositionProp(e.latlng);
        map.flyTo(e.latlng, map.getZoom());
    };

    const handleLocationError = e => {
        if (e.code === 1) {
            // User denied Geolocation
            setSnackbarOpen(true);
        }
    };

    const handleSnackbarClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }

        setSnackbarOpen(false);
    };

    useEffect(() => {
        map.on('locationfound', handleLocationFound);
        map.on('locationerror', handleLocationError);
        return () => {
            map.off('locationfound', handleLocationFound);
            map.off('locationerror', handleLocationError);
        };
    }, [map]);

    map.locate({ setView: false, maxZoom: 16, watch: true });

    const { lat, lng } = userPosition || {};
    const radius = (userPosition && userPosition.accuracy / 2) || 0;

    return (
        <>
            {userPosition && (
                <>
                    <CircleMarker center={[lat, lng]} radius={radius} />
                    <Marker position={userPosition} icon={createLocationIcon()} />
                </>
            )}
            <LocationButton userPosition={userPosition} map={map} />
            <Snackbar
                open={snackbarOpen}
                autoHideDuration={6000}
                onClose={handleSnackbarClose}
                message="Location access was denied. Please enable it in your browser settings to use this feature."
            />
        </>
    );
};

LocationControl.propTypes = {
    setUserPosition: PropTypes.func.isRequired,
};

export { LocationControl };
