/**
 * Adds the page's language to a goodmap API URL, as the `lang` query argument.
 *
 * platzky derives the locale from the request's host and path only, so an unprefixed
 * /api request would otherwise always be answered in the default language. Use it for
 * endpoints whose responses carry translated text.
 *
 * @param {string} url - API URL, with or without a query string
 * @returns {string} The URL with `lang` set to `APP_LANG`, or unchanged without one
 */
export const withLang = url => {
    const lang = globalThis.APP_LANG;
    if (!lang) {
        return url;
    }
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}lang=${encodeURIComponent(lang)}`;
};

/**
 * API endpoint for fetching all categories with their subcategories in a single request.
 * Eliminates the waterfall pattern of fetching categories then subcategories separately.
 */
export const CATEGORIES_FULL = '/api/categories-full';

/**
 * API endpoint describing what this deployment accepts for a new point:
 * the fields, their allowed values, reportable issue types and photo limits.
 */
export const LOCATION_SCHEMA = '/api/location-schema';

/**
 * API endpoint for fetching a single location by ID.
 * Use with location UUID appended: /api/location/{uuid}
 */
export const LOCATION = '/api/location';

/**
 * API endpoint for fetching all locations.
 * Supports query parameters for filtering.
 */
export const LOCATIONS = '/api/locations';

/**
 * API endpoint for fetching server-side clustered locations.
 * Supports query parameters for filtering and map configuration (zoom, bounds).
 */
export const LOCATIONS_CLUSTERED = '/api/locations-clustered';

/**
 * API endpoint for suggesting a new point.
 */
export const SUGGEST_NEW_POINT = '/api/suggest-new-point';

/**
 * API endpoint for reporting a problem with a location.
 */
export const REPORT_LOCATION = '/api/report-location';

/**
 * External API endpoint for address search (forward geocoding) using OpenStreetMap Nominatim.
 * Converts addresses/place names to geographic coordinates.
 */
export const SEARCH_ADDRESS = 'https://nominatim.openstreetmap.org/search';
