import React from 'react';

// The "MarkerField" capability's component. goodmap's FieldRenderer pipes field plugins from
// the field's raw value; every field plugin is a stage `({ input, config }) => element`. This
// one is the innermost/renderer stage: it gets the raw field data as `input` (e.g.
// `{ type: 'silly_gif', gif: '<url>' }`) and renders from it. It attaches to the 'silly_gif'
// field type via `config.field` (see the plugin config).
export default function SillyGifField({ input }) {
    return <img src={input.gif} alt="silly gif" style={{ maxWidth: 120, borderRadius: 8 }} />;
}
