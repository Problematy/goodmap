import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getPlugin, subscribe } from '../../plugins/pluginRegistry';
import getContentAsString from './fieldContent';
import { builtinFieldRenderers } from './builtinFieldRenderers';

// Built-in names a plugin also tried to claim; warned once each so the collision
// is visible to the author instead of silently shadowed.
const shadowedPlugins = new Set();

// TODO: add decorator capability to types.

/**
 * Resolves a field `type` to its renderer component: first-party built-ins take
 * precedence, then field-capability plugins (looked up by name in the registry).
 * A plugin registered under a built-in's name is shadowed by the built-in and
 * warned once, since that first-party precedence is deliberate (e.g. keeping the
 * URL-sanitizing link/button from being overridden).
 *
 * @param {string} type - The field's render type.
 * @returns {React.ComponentType|undefined} The renderer, or undefined if none is registered.
 */
export const resolveFieldRenderer = type => {
    const builtin = builtinFieldRenderers[type];
    if (builtin) {
        if (getPlugin(type) && !shadowedPlugins.has(type)) {
            shadowedPlugins.add(type);
            console.warn(
                `Field plugin "${type}" is shadowed by a built-in renderer of the same name; using the built-in.`,
            );
        }
        return builtin;
    }
    return getPlugin(type);
};

/**
 * Renders a marker field value.
 *
 * A value carrying a `type` is dispatched to its renderer — a built-in (hyperlink,
 * CTA) or a field plugin. Built-ins resolve synchronously; field plugins may load
 * asynchronously, so this subscribes to the registry and re-renders when a matching
 * plugin arrives. Anything with no resolvable renderer — a typeless object, a
 * primitive, or a not-yet-loaded plugin — falls back to a string representation.
 */
const FieldRenderer = ({ value }) => {
    const type = value?.type;
    const [Renderer, setRenderer] = useState(() => (type ? resolveFieldRenderer(type) : undefined));

    useEffect(() => {
        const resolve = () => setRenderer(() => (type ? resolveFieldRenderer(type) : undefined));
        resolve(); // re-resolve when `type` changes, not only on later registry events
        return subscribe(resolve);
    }, [type]);

    if (!Renderer) {
        return getContentAsString(type ? value.displayValue ?? value.value ?? '' : value);
    }
    // eslint-disable-next-line react/jsx-props-no-spreading
    return <Renderer {...value} />;
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
