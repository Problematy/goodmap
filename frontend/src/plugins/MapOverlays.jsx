import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getOverlayPlugins, subscribe } from './pluginRegistry';

// Renders map-overlay plugins (MapOverlayPluginBase): components mounted once over the
// map, not tied to any marker. Field-renderer plugins are mounted per marker by PluginSlot.
// Each overlay receives `config` and `isMapLoading` so it can defer rendering until the
// map's data has loaded (e.g. avoid flashing a "no points" message during the first fetch).
const MapOverlays = ({ isMapLoading }) => {
    const [plugins, setPlugins] = useState(() => getOverlayPlugins());

    useEffect(() => subscribe(() => setPlugins(getOverlayPlugins())), []);

    return (
        <>
            {plugins.map(([pluginName, Plugin, config]) => (
                <Plugin key={pluginName} config={config} isMapLoading={isMapLoading} />
            ))}
        </>
    );
};

MapOverlays.propTypes = {
    isMapLoading: PropTypes.bool.isRequired,
};

export default MapOverlays;
