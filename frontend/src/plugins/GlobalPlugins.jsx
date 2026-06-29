import React, { useState, useEffect } from 'react';
import { getAllPlugins, subscribe } from './pluginRegistry';

const GlobalPlugins = () => {
    const [plugins, setPlugins] = useState(() => getAllPlugins());

    useEffect(() => subscribe(() => setPlugins(getAllPlugins())), []);

    return (
        <>
            {plugins.map(([scope, Component]) => (
                <Component key={scope} />
            ))}
        </>
    );
};

export default GlobalPlugins;
