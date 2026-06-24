import {
    CATEGORIES,
    CATEGORIES_FULL,
    CATEGORY,
    LANGUAGES,
    LOCATION,
    LOCATIONS,
    SEARCH_ADDRESS,
    LOCATIONS_CLUSTERED,
} from './endpoints';
import { useMapStore } from '../../components/Map/store/map.store';

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
     * Fetches all available categories.
     *
     * @returns {Promise<Object>} Promise resolving to categories data
     */
    getCategories: () => fetch(CATEGORIES).then(response => response.json()),

    /**
     * Fetches subcategories for a specific category.
     *
     * @param {string} category - Category name
     * @returns {Promise<Object>} Promise resolving to subcategories data
     */
    getSubcategories: category =>
        fetch(`${CATEGORY}/${category}`).then(response => response.json()),

    /**
     * Fetches complete categories data including subcategories in a single request.
     * Uses the /api/categories-full endpoint to avoid waterfall requests.
     *
     * @returns {Promise<Array>} Promise resolving to array of category data tuples
     */
    getCategoriesData: async () => {
        const response = await fetch(CATEGORIES_FULL).then(res => res.json());

        // Transform to expected format: [[key, name], options, help?, optionsHelp?]
        return response.categories.map(category => {
            const categoryTuple = [category.key, category.name];
            const options = category.options;

            if (globalThis.FEATURE_FLAGS?.CATEGORIES_HELP) {
                return [
                    categoryTuple,
                    category.options_with_help ?? options,
                    response.categories_help ?? [],
                    category.options_help ?? [],
                ];
            }
            return [categoryTuple, options];
        });
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
        const response = await fetch(`${LOCATION}/${locationId}`, {
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
     * Fetches available languages for the application.
     *
     * @returns {Promise<Array>} Promise resolving to array of language objects
     */
    getLanguages: () => fetch(LANGUAGES).then(response => response.json()),

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
