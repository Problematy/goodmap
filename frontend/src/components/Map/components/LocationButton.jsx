import React from 'react';
import { useMap } from 'react-leaflet';
import PropTypes from 'prop-types';
import Control from 'react-leaflet-custom-control';
import { Button, Box } from '@mui/material';
import MyLocationIcon from '@mui/icons-material/MyLocation';

const LocationButton = ({ userPosition = null }) => {
    const map = useMap();

    const handleFlyToLocationClick = () => {
        if (!userPosition) {
            map.locate({ setView: true, maxZoom: 16 });
        } else {
            const zoomLevel = map.getZoom() < 16 ? 16 : map.getZoom();
            map.flyTo(userPosition, zoomLevel);
        }
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

const positionType = PropTypes.shape({
    lat: PropTypes.number.isRequired,
    lng: PropTypes.number.isRequired,
});

LocationButton.propTypes = {
    userPosition: positionType,
};

export { LocationButton };
