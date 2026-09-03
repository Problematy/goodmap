import React, { useReducer, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getFieldPlugins, subscribe } from '../../plugins/pluginRegistry';
import getContentAsString from './fieldContent';
import ServerHtmlField from './serverHtmlField';

/**
 * Renders a marker field value as a pipe.
 *
 * The raw `value` flows through a chain of stages: the server-rendered `html` seeds the fold,
 * then each field plugin attached to that `type` (by `config.field`) transforms the result,
 * innermost-first by `config.order`. Every stage is `({ input, config }) => element` taking
 * the previous stage's output as `input`, so the innermost renders from the raw value and
 * each later one wraps the current element. A type with only wrappers and no renderer is a
 * misconfiguration; with no stage at all the value falls back to a string.
 *
 * Plugins load asynchronously, so this subscribes to the registry and re-renders as they
 * arrive. Everything else is computed during render.
 */
const FieldRenderer = ({ value }) => {
    const [, forceRender] = useReducer(count => count + 1, 0);
    useEffect(() => subscribe(forceRender), []);

    const type = value?.type;
    const plugins = type ? getFieldPlugins(type) : [];

    // Whatever rendered the field server-side seeds the fold with its own HTML, which is what
    // lets goodmap's built-in types and a platzky plugin alike display with no frontend code.
    // The seed is always there for a rendered type, so wrappers can only wrap it.
    //
    // Presence, not truthiness: a shortcode rendering an empty string still rendered the
    // field, and dropping the seed would hand a wrapper the raw value object where its
    // contract promises the previous stage's element.
    const Seed = typeof value?.html === 'string' ? ServerHtmlField : undefined;

    const stages = [
        ...(Seed ? [{ Stage: Seed, config: undefined }] : []),
        ...plugins.map(({ Plugin, config }) => ({ Stage: Plugin, config })),
    ];

    if (stages.length === 0) {
        return getContentAsString(type ? value.displayValue ?? value.value ?? '' : value);
    }

    return stages.reduce(
        (input, { Stage, config }) => <Stage input={input} config={config} />,
        value,
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
