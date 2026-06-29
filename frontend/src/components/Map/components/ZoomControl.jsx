import React from 'react';
import { useMap } from 'react-leaflet';
import Control from 'react-leaflet-custom-control';
import { Button } from '@mui/material';
import { zoomInButtonStyle, zoomOutButtonStyle } from '../../../styles/buttonStyle';

/**
 * Custom zoom control component for the Leaflet map.
 * Renders stacked zoom in (+) and zoom out (-) buttons in the top-right corner of the map.
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
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <Button
                    onClick={handleZoomIn}
                    variant="contained"
                    aria-label="Zoom in"
                    sx={zoomInButtonStyle}
                >
                    +
                </Button>
                <Button
                    onClick={handleZoomOut}
                    variant="contained"
                    aria-label="Zoom out"
                    sx={zoomOutButtonStyle}
                >
                    −
                </Button>
            </div>
        </Control>
    );
};
