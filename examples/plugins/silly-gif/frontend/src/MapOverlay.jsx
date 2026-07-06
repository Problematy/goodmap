import React from 'react';

// The "MapOverlay" capability's component. goodmap's MapOverlays mounts it once over the map
// and passes the plugin `config` plus `isMapLoading`. Here we show the gif (from config)
// only while the map's data is loading.
export default function SillyGifOverlay({ config, isMapLoading }) {
    if (!isMapLoading) return null;
    return (
        <img
            src={config.gif}
            alt="loading"
            style={{
                position: 'absolute',
                bottom: 16,
                right: 16,
                width: 96,
                zIndex: 1000,
                pointerEvents: 'none',
            }}
        />
    );
}
