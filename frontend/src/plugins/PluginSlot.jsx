import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getPlugin, subscribe } from './pluginRegistry';

const PluginSlot = ({ pluginName, props: componentProps }) => {
    const [Plugin, setPlugin] = useState(() => getPlugin(pluginName));

    useEffect(() => subscribe(() => setPlugin(() => getPlugin(pluginName))), [pluginName]);

    if (!Plugin) {
        return null;
    }
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <Plugin {...componentProps} />;
};

PluginSlot.propTypes = {
    pluginName: PropTypes.string.isRequired,
    props: PropTypes.object.isRequired, // eslint-disable-line react/forbid-prop-types
};

export default PluginSlot;
