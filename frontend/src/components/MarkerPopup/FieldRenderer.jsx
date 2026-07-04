import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getPlugin, getFieldDecorators, subscribe } from '../../plugins/pluginRegistry';
import getContentAsString from './fieldContent';
import { builtinFieldRenderers } from './builtinFieldRenderers';

// Built-in names a plugin also tried to claim; warned once each so the collision
// is visible to the author instead of silently shadowed.
const shadowedPlugins = new Set();

/**
 * Resolves a field `type` to its renderer component: first-party built-ins take
 * precedence, then field-capability plugins (looked up by name in the registry).
 * A plugin registered under a built-in's name is shadowed by the built-in and
 * warned once — that first-party precedence is deliberate (e.g. keeping the
 * URL-sanitizing link/button from being replaced). To customize a built-in's
 * rendering, register a field-decorator for the type instead of overriding it.
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
                `Field plugin "${type}" is shadowed by a built-in renderer of the same name; ` +
                    `use a field-decorator to wrap the built-in instead.`,
            );
        }
        return builtin;
    }
    return getPlugin(type);
};

// Resolves the renderer plus any decorators registered for a `type` in one shot, so
// FieldRenderer re-resolves both together on a `type` change or a registry event.
const resolveField = type => ({
    Renderer: type ? resolveFieldRenderer(type) : undefined,
    decorators: type ? getFieldDecorators(type) : [],
});

/**
 * Renders a marker field value.
 *
 * A value carrying a `type` is dispatched to its renderer — a built-in (hyperlink,
 * CTA) or a field plugin. Built-ins resolve synchronously; field plugins may load
 * asynchronously, so this subscribes to the registry and re-renders when a matching
 * plugin arrives. Anything with no resolvable renderer — a typeless object, a
 * primitive, or a not-yet-loaded plugin — falls back to a string representation.
 *
 * Field decorators registered for the `type` then wrap the rendered output as their
 * `children` (composing in registration order). The base renderer still runs, so
 * first-party behaviour like the built-in link/button URL sanitization is preserved.
 */
const FieldRenderer = ({ value }) => {
    const type = value?.type;
    const [{ Renderer, decorators }, setResolved] = useState(() => resolveField(type));

    useEffect(() => {
        const resolve = () => setResolved(resolveField(type));
        resolve(); // re-resolve when `type` changes, not only on later registry events
        return subscribe(resolve);
    }, [type]);

    const base = Renderer ? (
        // eslint-disable-next-line react/jsx-props-no-spreading
        <Renderer {...value} />
    ) : (
        getContentAsString(type ? value.displayValue ?? value.value ?? '' : value)
    );

    return decorators.reduce(
        (child, { Decorator, config }) => <Decorator config={config}>{child}</Decorator>,
        base,
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
