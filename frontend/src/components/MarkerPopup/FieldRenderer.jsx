import React, { useReducer, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getFieldPlugins, subscribe } from '../../plugins/pluginRegistry';
import getContentAsString from './fieldContent';
import { builtinFieldRenderers } from './builtinFieldRenderers';

/**
 * Renders a marker field value as a pipe.
 *
 * The raw `value` flows through a chain of stages: the built-in for the field `type` (if
 * any) renders it into an element, then each field plugin attached to that `type` (by
 * `config.field`) transforms the result, innermost-first by `config.order`. Every stage is
 * `({ input, config }) => element`, receiving the previous stage's output as `input` — so
 * the innermost gets the raw value and renders from it, and each later stage gets the
 * current element and wraps it.
 *
 * A wrapper therefore presupposes that something renders the type (a built-in, or a renderer
 * plugin it ships with / depends on); a type with only wrappers and no renderer is a
 * misconfiguration. With no stage at all, the value falls back to a string.
 *
 * Everything is computed during render, so a changed `value`/`type` is always reflected;
 * plugins load asynchronously, so this subscribes to the registry and forces a re-render as
 * they arrive.
 */
const FieldRenderer = ({ value }) => {
    const [, forceRender] = useReducer(count => count + 1, 0);
    useEffect(() => subscribe(forceRender), []);

    const type = value?.type;
    const Builtin = type ? builtinFieldRenderers[type] : undefined;
    const plugins = type ? getFieldPlugins(type) : [];

    const stages = [
        ...(Builtin ? [{ Stage: Builtin, config: undefined }] : []),
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
