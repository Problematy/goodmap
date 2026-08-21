const PHOSPHOR_ICONS_CDN_BASE = 'https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill';

/**
 * Resolves a phosphor icon name (kebab-case, e.g. "shipping-container") to its
 * "fill" weight SVG URL on the Phosphor Icons CDN (MIT-licensed, jsdelivr-hosted).
 * Not validated against the actual icon set - an unknown name just 404s in the
 * browser when the mask-image is requested, same as any other misconfigured URL.
 *
 * @param {string} name - Icon name, matching a filename in
 *   @phosphor-icons/core/assets/fill without its "-fill.svg" suffix
 * @returns {string} The icon's CDN URL
 */
const resolvePhosphorIconUrl = name => `${PHOSPHOR_ICONS_CDN_BASE}/${name}-fill.svg`;

export default resolvePhosphorIconUrl;
