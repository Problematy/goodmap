import React from 'react';

// The "MarkerField" capability's component. goodmap's FieldRenderer folds field plugins
// around a marker field; every field plugin receives `{ value, children, config }`. This one
// acts as a *renderer*: it renders from `value` (the field data, e.g.
// `{ type: 'silly_gif', gif: '<url>' }`) and ignores `children`. It attaches to the
// 'silly_gif' field type via `config.field` (see the plugin config).
export default function SillyGifField({ value }) {
    return <img src={value.gif} alt="silly gif" style={{ maxWidth: 120, borderRadius: 8 }} />;
}
