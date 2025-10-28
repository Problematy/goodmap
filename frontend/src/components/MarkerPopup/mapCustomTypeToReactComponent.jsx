import React from 'react';
import { MarkerCTAButtonStyle } from '../../styles/buttonStyle';

/**
 * Converts data to a string representation.
 * Arrays are joined with comma-space separator, other values are converted to string.
 *
 * @param {*} data - Data to convert to string
 * @returns {string} Joined string if array, otherwise the data converted to string
 */
export const getContentAsString = data =>
    Array.isArray(data) ? data.join(', ') : String(data ?? '');

/**
 * Sanitizes URLs to prevent javascript: or data: injection attacks.
 * Only allows http:, https:, mailto:, and tel: protocols.
 *
 * @param {*} raw - Raw URL to sanitize
 * @returns {string|null} Sanitized URL or null if invalid/unsafe
 */
const sanitizeUrl = raw => {
    try {
        // Use globalThis.location.origin as base, with fallback for non-browser environments
        const base = globalThis.location?.origin || 'http://localhost';
        const url = new URL(String(raw), base);
        const allowed = new Set(['http:', 'https:', 'mailto:', 'tel:']);
        return allowed.has(url.protocol) ? url.href : null;
    } catch {
        return null;
    }
};

/**
 * Maps custom typed values to appropriate React components.
 * Supports hyperlinks and CTA (Call-To-Action) buttons.
 *
 * @param {Object} customValue - Custom value object with type and value properties
 * @param {string} customValue.type - Type of custom value ('hyperlink' or 'CTA')
 * @param {string} customValue.value - URL or value to use
 * @param {string} [customValue.displayValue] - Optional display text (falls back to value)
 * @returns {React.ReactElement|string} React component for the custom type or string content
 * @throws {Error} If customValue is missing type or value properties
 */
export const mapCustomTypeToReactComponent = customValue => {
    if (!customValue.type || !customValue.value) {
        throw new Error('Custom value must have type and value properties');
    }

    const valueToDisplay = customValue?.displayValue || customValue.value;

    switch (customValue.type) {
        case 'hyperlink': {
            const safe = sanitizeUrl(customValue.value);
            if (!safe) return valueToDisplay;
            return (
                <a href={safe} rel="noreferrer noopener" target="_blank">
                    {valueToDisplay}
                </a>
            );
        }
        case 'CTA': {
            const handleRedirect = () => {
                const safe = sanitizeUrl(customValue.value);
                if (!safe) return;
                globalThis.open(safe, '_blank');
            };
            return (
                <button
                    type="button"
                    onClick={handleRedirect}
                    style={MarkerCTAButtonStyle}
                    data-variant="contained"
                >
                    {valueToDisplay}
                </button>
            );
        }
        default:
            return getContentAsString(valueToDisplay);
    }
};
