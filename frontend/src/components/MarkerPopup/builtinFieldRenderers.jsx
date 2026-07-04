import React from 'react';
import PropTypes from 'prop-types';
import { MarkerCTAButtonStyle } from '../../styles/buttonStyle';

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
 * Built-in field renderer: a safe external hyperlink.
 * Falls back to plain text when the URL is unsafe.
 */
export const HyperlinkField = ({ value, displayValue = null }) => {
    const text = displayValue || value;
    const safe = sanitizeUrl(value);
    if (!safe) return text;
    return (
        <a href={safe} rel="noreferrer noopener" target="_blank">
            {text}
        </a>
    );
};

HyperlinkField.propTypes = {
    value: PropTypes.string.isRequired,
    displayValue: PropTypes.string,
};

/**
 * Built-in field renderer: a call-to-action button that opens the (sanitized)
 * URL in a new tab.
 */
export const CTAButtonField = ({ value, displayValue = null }) => {
    const handleRedirect = () => {
        const safe = sanitizeUrl(value);
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
            {displayValue || value}
        </button>
    );
};

CTAButtonField.propTypes = {
    value: PropTypes.string.isRequired,
    displayValue: PropTypes.string,
};

// Built-in field renderers, keyed by field `type`. Resolved before plugins so a
// plugin cannot shadow a first-party renderer (e.g. the URL-sanitizing link/button).
export const builtinFieldRenderers = {
    hyperlink: HyperlinkField,
    CTA: CTAButtonField,
};
