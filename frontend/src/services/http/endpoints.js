/**
 * API endpoint for fetching all categories.
 */
export const CATEGORIES = '/api/categories';

/**
 * API endpoint for fetching all categories with their subcategories in a single request.
 * Eliminates the waterfall pattern of fetching categories then subcategories separately.
 */
export const CATEGORIES_FULL = '/api/categories-full';

/**
 * API endpoint for fetching subcategories for a specific category.
 * Use with category name appended: /api/category/{categoryName}
 */
export const CATEGORY = '/api/category';

/**
 * API endpoint for fetching available languages.
 */
export const LANGUAGES = '/api/languages';

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

/**
 * External API endpoint for reverse geocoding using OpenStreetMap Nominatim.
 * Converts geographic coordinates to addresses/place names.
 */
export const REVERSE_ADDRESS = 'https://nominatim.openstreetmap.org/reverse';
