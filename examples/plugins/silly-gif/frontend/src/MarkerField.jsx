import React from 'react';

// The "field" capability's component. goodmap's FieldRenderer mounts it for a marker field
// whose value is `{ type: 'silly_gif', gif: '<url>' }`, spreading that value object as props.
// Note the contract differs from the overlay: a field component receives the *field value*
// (each marker can carry its own gif), not the plugin `config`.
export default function SillyGifField({ gif }) {
    return <img src={gif} alt="silly gif" style={{ maxWidth: 120, borderRadius: 8 }} />;
}
