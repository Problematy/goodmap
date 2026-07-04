import React from 'react';
import getContentAsString from './fieldContent';
import FieldRenderer from './FieldRenderer';

// Re-exported for existing consumers (e.g. LocationDetails) that import it from here.
export { getContentAsString };

/**
 * Renders a custom typed marker field value.
 *
 * Fields carrying a `type` are dispatched to their renderer — a built-in
 * (hyperlink, CTA) or a field plugin — via FieldRenderer. Typeless values fall
 * back to a string representation.
 *
 * @param {Object} customValue - Field value object; `type` selects the renderer.
 * @returns {React.ReactElement|string} Rendered field, or string content.
 */
export const mapCustomTypeToReactComponent = customValue => {
    if (customValue?.type) {
        return <FieldRenderer type={customValue.type} props={customValue} />;
    }
    return getContentAsString(customValue);
};
