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
 * External API endpoint for address search (forward geocoding) using OpenStreetMap Nominatim.
 * Converts addresses/place names to geographic coordinates.
 */
export const SEARCH_ADDRESS = 'https://nominatim.openstreetmap.org/search';
