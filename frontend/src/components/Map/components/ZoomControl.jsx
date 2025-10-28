import React from 'react';
import { useMap } from 'react-leaflet';
import Control from 'react-leaflet-custom-control';
import { Button, Divider } from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn'; // Zoom in icon
import ZoomOutIcon from '@mui/icons-material/ZoomOut'; // Zoom out icon
import { zoomButtonStyle } from '../../../styles/buttonStyle';

/**
 * Custom zoom control component for the Leaflet map.
 * Renders zoom in and zoom out buttons in the top-right corner of the map.
 * Provides a styled alternative to the default Leaflet zoom controls.
 *
 * @returns {React.ReactElement} Control component with zoom in/out buttons
 */
export const CustomZoomControl = () => {
    const map = useMap();

    const handleZoomIn = () => {
        map.zoomIn();
    };

    const handleZoomOut = () => {
        map.zoomOut();
    };

    return (
        <Control prepend position="topright">
            <Button style={zoomButtonStyle} variant="contained">
                <ZoomInIcon
                    onClick={handleZoomIn}
                    style={{ color: 'white', fontSize: 35, marginRight: '10px' }}
                />{' '}
                <Divider orientation="vertical" flexItem style={{ backgroundColor: 'white' }} />
                <ZoomOutIcon
                    onClick={handleZoomOut}
                    style={{ color: 'white', fontSize: 35, marginLeft: '10px' }}
                />{' '}
            </Button>
        </Control>
    );
};
