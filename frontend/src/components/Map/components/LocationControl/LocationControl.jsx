import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Marker, CircleMarker, useMap } from 'react-leaflet';
import { Button, Box } from '@mui/material';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import Control from 'react-leaflet-custom-control';
import ReactDOMServer from 'react-dom/server';
import L from 'leaflet';

const LocationButton = ({ userPosition }) => {
    const map = useMap();

    const handleFlyToLocationClick = () => {
        map.flyTo(userPosition, map.getZoom());
    };

    return (
        <Control prepend position="bottomright">
            <Button onClick={handleFlyToLocationClick}>
                <Box
                    sx={{
                        boxShadow: 1.3,
                        border: 0.1,
                        color: 'black',
                        padding: 0.5,
                        background: 'white',
                    }}
                >
                    <MyLocationIcon sx={{ color: 'black', fontSize: 22 }} />
                </Box>
            </Button>
        </Control>
    );
};

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

const LocationControl = () => {
    const [userPosition, setUserPosition] = useState(null);
    const map = useMap();

    const handleLocationFound = e => {
        setUserPosition(e.latlng);
        map.flyTo(e.latlng, map.getZoom());
    };

    map.once('locationfound', handleLocationFound);

    map.locate({ setView: false, maxZoom: 16, watch: true });

    if (!userPosition) {
        return null;
    }

    const { lat, lng } = userPosition;
    const radius = userPosition.accuracy / 2 || 0;

    return (
        <>
            <LocationButton userPosition={userPosition} />
            <CircleMarker center={[lat, lng]} radius={radius} />
            <Marker position={userPosition} icon={createLocationIcon()} />
        </>
    );
};

export { LocationControl };

const positionType = PropTypes.shape({
    lat: PropTypes.number.isRequired,
    lng: PropTypes.number.isRequired,
});

LocationButton.propTypes = {
    userPosition: positionType.isRequired,
};
