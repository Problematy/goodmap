import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getFieldPlugins, subscribe } from '../../plugins/pluginRegistry';
import getContentAsString from './fieldContent';
import { builtinFieldRenderers } from './builtinFieldRenderers';

/**
 * Renders a marker field value as a fold.
 *
 * A *seed* rendering is produced first — the first-party built-in for the field `type`
 * (rendered from the value), or a string rendering of the value when there is none. Then
 * every field plugin that attaches to that `type` (via `config.field`) wraps the result,
 * innermost-first by `config.order`.
 *
 * Every field plugin is the same kind of thing: a wrapper receiving `{ value, children,
 * config }` — it may render from `value` (ignoring `children`) or compose around
 * `children`. Plugins load asynchronously, so this subscribes to the registry and
 * re-renders as they arrive (and re-resolves when `type` changes).
 */
const FieldRenderer = ({ value }) => {
    const type = value?.type;
    const [plugins, setPlugins] = useState(() => (type ? getFieldPlugins(type) : []));

    useEffect(() => {
        const update = () => setPlugins(type ? getFieldPlugins(type) : []);
        update(); // re-resolve when `type` changes, not only on later registry events
        return subscribe(update);
    }, [type]);

    const Builtin = type ? builtinFieldRenderers[type] : undefined;
    const seed = Builtin ? (
        // eslint-disable-next-line react/jsx-props-no-spreading
        <Builtin {...value} />
    ) : (
        getContentAsString(type ? value.displayValue ?? value.value ?? '' : value)
    );

    return plugins.reduce(
        (children, { Plugin, config }) => (
            <Plugin value={value} config={config}>
                {children}
            </Plugin>
        ),
        seed,
    );
};

FieldRenderer.propTypes = {
    value: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.array,
        PropTypes.object,
    ]).isRequired,
};

export default FieldRenderer;
