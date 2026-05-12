import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getPlugin, subscribe } from './pluginRegistry';

const PluginSlot = ({ scope, props: componentProps }) => {
    const [Component, setComponent] = useState(() => getPlugin(scope));

    useEffect(() => subscribe(() => setComponent(() => getPlugin(scope))), [scope]);

    if (!Component) {
        return null;
    }
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <Component {...componentProps} />;
};

PluginSlot.propTypes = {
    scope: PropTypes.string.isRequired,
    props: PropTypes.object, // eslint-disable-line react/forbid-prop-types
};

PluginSlot.defaultProps = {
    props: {},
};

export default PluginSlot;
