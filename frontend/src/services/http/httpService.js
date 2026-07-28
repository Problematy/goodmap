import {
    CATEGORIES_FULL,
    LOCATION,
    LOCATIONS,
    SEARCH_ADDRESS,
    LOCATIONS_CLUSTERED,
} from './endpoints';
import { useMapStore } from '../../components/Map/store/map.store';

// UUID allowlist used to validate location ids before they are placed in a
// request URL. An inline regex (not uuid.validate()) is used deliberately:
// SonarQube's taint analysis only recognises regex/allowlist checks as
// sanitizers for request-URL construction, not third-party validators.
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Converts filter object to URL query string parameters.
 * Also includes map configuration (zoom, bounds) if server-side clustering is enabled.
 *
 * @param {Object} filters - Filter object with category keys and array values
 * @returns {string} URL-encoded query string
 */
function filtersToQuery(filters) {
    const params = new URLSearchParams();
    for (const [key, values = []] of Object.entries(filters || {})) {
        for (const value of values) {
            params.append(key, String(value));
        }
    }
    if (globalThis.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING) {
        const mapConfigurationData = useMapStore.getState().mapConfiguration;
        if (mapConfigurationData) {
            for (const [k, v] of Object.entries(mapConfigurationData)) {
                params.append(String(k), String(v));
            }
        }
    }
    return params.toString();
}

/**
 * HTTP service object containing all API interaction methods.
 * Provides methods for fetching categories, locations, languages, and address search.
 */
export const httpService = {
    /**
     * Fetches complete categories data including subcategories in a single request.
     * Uses the /api/categories-full endpoint to avoid waterfall requests.
     *
     * @returns {Promise<{categories: Array<{categoryKey: string, categoryName: string,
     *   options: Array<[string, string]>, categoriesHelp: Array, optionsHelp: Array,
     *   filterMode: string}>, defaultChecked: Object}>} Promise resolving to the array of
     *   category data plus a map of category key to the option values that should be
     *   pre-checked by default.
     */
    getCategoriesData: async () => {
        const response = await fetch(CATEGORIES_FULL).then(res => res.json());
        const useCategoriesHelp = Boolean(globalThis.FEATURE_FLAGS?.CATEGORIES_HELP);

        const categories = response.categories.map(category => ({
            categoryKey: category.key,
            categoryName: category.name,
            options: (useCategoriesHelp ? category.options_with_help : null) ?? category.options,
            categoriesHelp: useCategoriesHelp ? response.categories_help ?? [] : [],
            optionsHelp: useCategoriesHelp ? category.options_help ?? [] : [],
            filterMode: category.filter_mode ?? 'or',
        }));

        const defaultChecked = Object.fromEntries(
            response.categories
                .filter(category => category.default_checked?.length)
                .map(category => [category.key, category.default_checked]),
        );

        return { categories, defaultChecked };
    },

    /**
     * Fetches locations based on filter criteria.
     * Uses server-side clustering if enabled via feature flags.
     *
     * @param {Object} filters - Filter object with category keys and array values
     * @returns {Promise<Array>} Promise resolving to array of location objects
     */
    getLocations: async filters => {
        const filtersUrlParams = filtersToQuery(filters);

        let ENDPOINT = LOCATIONS;
        if (globalThis.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING) {
            ENDPOINT = LOCATIONS_CLUSTERED;
        }

        const response = await fetch(`${ENDPOINT}?${filtersUrlParams}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        return response.json();
    },

    /**
     * Fetches locations near a specific geographic coordinate with filtering.
     * Results are limited to 10 locations closest to the provided coordinates.
     *
     * @param {number} lat - Latitude coordinate
     * @param {number} lon - Longitude coordinate
     * @param {Object} filters - Filter object with category keys and array values
     * @returns {Promise<Array>} Promise resolving to array of nearby location objects
     */
    getLocationsWithLatLon: async (lat, lon, filters) => {
        const filtersUrlParams = filtersToQuery(filters);
        const response = await fetch(
            `${LOCATIONS}?${filtersUrlParams}&lat=${lat}&lon=${lon}&limit=10`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            },
        );
        return response.json();
    },

    /**
     * Fetches detailed information for a single location by its UUID.
     *
     * @param {string} locationId - UUID of the location
     * @returns {Promise<Object>} Promise resolving to location details object
     */
    getLocation: async locationId => {
        // SECURITY: locationId can come from a user-controlled URL param (see
        // GoToLocation). Require a valid UUID and encode it before building the
        // request URL, to prevent request-URL injection.
        const id = String(locationId);
        if (!UUID_RE.test(id)) {
            throw new Error('Invalid locationId: expected a UUID');
        }

        const response = await fetch(`${LOCATION}/${encodeURIComponent(id)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        return response.json();
    },

    /**
     * Fetches detailed data for multiple locations near a coordinate.
     * First fetches nearby location UUIDs, then fetches full details for each location.
     *
     * @param {number} lat - Latitude coordinate
     * @param {number} lon - Longitude coordinate
     * @param {Object} filters - Filter object with category keys and array values
     * @returns {Promise<Array>} Promise resolving to array of detailed location objects
     * @throws {Error} If fetching location data fails
     */
    getLocationsData: async (lat, lon, filters) => {
        const locations = await httpService.getLocationsWithLatLon(lat, lon, filters);
        try {
            const dataPromises = locations.map(location => httpService.getLocation(location.uuid));
            return await Promise.all(dataPromises);
        } catch (error) {
            console.error('Failed to fetch location data:', error);
            throw error;
        }
    },

    /**
     * Searches for addresses using OpenStreetMap Nominatim API.
     * Returns up to 5 results with geocoded coordinates.
     *
     * @param {string} search - Search query string
     * @returns {Promise<Array>} Promise resolving to array of address search results
     */
    getSearchAddress: search => {
        const params = {
            format: 'json',
            limit: 5,
            q: search,
            'accept-language': globalThis.APP_LANG || 'pl',
        };

        const queryString = new URLSearchParams(params).toString();

        return fetch(`${SEARCH_ADDRESS}?${queryString}`).then(response => response.json());
    },
};
