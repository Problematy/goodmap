import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Marker, CircleMarker, useMap } from 'react-leaflet';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import ReactDOMServer from 'react-dom/server';
import L from 'leaflet';
import { Snackbar, Button } from '@mui/material';
import { buttonStyle } from '../../../styles/buttonStyle';
import Control from 'react-leaflet-custom-control';

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

    const flyToLocation = (location, mapInstance) => {
        const zoomLevel = mapInstance.getZoom() < 16 ? 16 : mapInstance.getZoom();
        mapInstance.flyTo(location, zoomLevel);
    };

    const handleLocationFound = e => {
        setUserPosition(e.latlng);
        setUserPositionProp(e.latlng);
        flyToLocation(e.latlng, map);
    };

    const handleLocationError = e => {
        if (e.code === 1) {
            // User denied Geolocation
            setSnackbarOpen(true);
            setUserPosition(null);
        }
        map.stopLocate();
    };

    const handleSnackbarClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }
        setSnackbarOpen(false);
    };

    const handleFlyToLocationClick = () => {
        map.locate({ setView: false, maxZoom: 16, watch: true });
        if (userPosition) {
            flyToLocation(userPosition, map);
        }
    };

    useEffect(() => {
        map.on('locationfound', handleLocationFound);
        map.on('locationerror', handleLocationError);

        return () => {
            map.off('locationfound', handleLocationFound);
            map.off('locationerror', handleLocationError);
        };
    }, [map]);

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
            <Control prepend position="bottomright">
                <Button onClick={handleFlyToLocationClick} style={buttonStyle} variant="contained">
                    <MyLocationIcon style={{ color: 'white', fontSize: 24 }} />
                </Button>

                <Snackbar
                    open={snackbarOpen}
                    autoHideDuration={4000}
                    onClose={handleSnackbarClose}
                    message="Please enable location services to see your location on the map."
                />
            </Control>
        </>
    );
};

LocationControl.propTypes = {
    setUserPosition: PropTypes.func.isRequired,
};

export { LocationControl };
