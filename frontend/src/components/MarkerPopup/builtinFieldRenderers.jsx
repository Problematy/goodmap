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

// Built-ins are the innermost stage of the field fold: they receive the field's raw value
// as `input` (`{ value, displayValue, ... }`) and render it into an element.
const fieldInputShape = PropTypes.shape({
    value: PropTypes.string.isRequired,
    displayValue: PropTypes.string,
});

/**
 * Built-in field renderer: a safe external hyperlink.
 * Falls back to plain text when the URL is unsafe.
 */
export const HyperlinkField = ({ input }) => {
    const { value, displayValue } = input;
    const text = displayValue || value;
    const safe = sanitizeUrl(value);
    if (!safe) return text;
    return (
        <a href={safe} rel="noreferrer noopener" target="_blank">
            {text}
        </a>
    );
};

HyperlinkField.propTypes = { input: fieldInputShape.isRequired };

/**
 * Built-in field renderer: a call-to-action button that opens the (sanitized)
 * URL in a new tab.
 */
export const CTAButtonField = ({ input }) => {
    const { value, displayValue } = input;
    const text = displayValue || value;
    const safe = sanitizeUrl(value);
    if (!safe) return text;
    const handleRedirect = () => globalThis.open(safe, '_blank');
    return (
        <button
            type="button"
            onClick={handleRedirect}
            style={MarkerCTAButtonStyle}
            data-variant="contained"
        >
            {text}
        </button>
    );
};

CTAButtonField.propTypes = { input: fieldInputShape.isRequired };

/**
 * Renders the HTML a platzky shortcode produced for its own field value.
 *
 * The markup is not sanitized, and deliberately so: it comes from an installed plugin
 * package, which already runs arbitrary code in the server process — the same trust
 * platzky extends to shortcode output in post content. Sanitizing would filter nothing a
 * plugin could not do more directly, while breaking legitimate markup. The plugin's
 * obligation in return is to escape the *data* it interpolates, which is untrusted.
 *
 * Never reached for a `type` that has a first-party renderer, so a plugin cannot use it
 * to take over `hyperlink` or `CTA`.
 */
export const PluginHtmlField = ({ input }) => (
    <span dangerouslySetInnerHTML={{ __html: input.html }} />
);

PluginHtmlField.propTypes = {
    input: PropTypes.shape({ html: PropTypes.string.isRequired }).isRequired,
};

// Built-in field renderers, keyed by field `type`. Resolved before plugins so a
// plugin cannot shadow a first-party renderer (e.g. the URL-sanitizing link/button).
export const builtinFieldRenderers = {
    hyperlink: HyperlinkField,
    CTA: CTAButtonField,
};
