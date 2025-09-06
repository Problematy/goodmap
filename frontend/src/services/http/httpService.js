import {
    CATEGORIES,
    CATEGORY,
    LANGUAGES,
    LOCATION,
    LOCATIONS,
    SEARCH_ADDRESS,
    LOCATIONS_CLUSTERED,
} from './endpoints';
import { useMapStore } from '../../components/Map/store/map.store';

function filtersToQuery(filters) {
    const params = new URLSearchParams();
    Object.entries(filters || {}).forEach(([key, values = []]) => {
        values.forEach(value => params.append(key, String(value)));
    });
    if (window.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING) {
        const mapConfigurationData = useMapStore.getState().mapConfiguration;
        if (mapConfigurationData) {
            Object.entries(mapConfigurationData).forEach(([k, v]) =>
                params.append(String(k), String(v)),
            );
        }
    }
    return params.toString();
}

export const httpService = {
    getCategories: () => fetch(CATEGORIES).then(response => response.json()),

    getSubcategories: category =>
        fetch(`${CATEGORY}/${category}`).then(response => response.json()),

    getCategoriesData: async () => {
        const categories = await httpService.getCategories();
        const categories_ = window.FEATURE_FLAGS?.CATEGORIES_HELP ? categories.categories : categories

        const subcategoriesPromises = categories_.map(([categoryName, _translation]) =>
            httpService.getSubcategories(categoryName),
        );
        const subcategoriesResponse = Promise.all(subcategoriesPromises);

        const mainResponse = subcategoriesResponse.then(subcategories => {
            if (window.FEATURE_FLAGS?.CATEGORIES_HELP) {
                return categories_.map((subcategory, index) => [
                    subcategory,
                    subcategories[index].categories_options ?? null,
                    categories.categories_help,
                    subcategories[index].categories_options_help ?? null,
                ])
                } else {
                    return categories_.map((subcategory, index) => [
                        subcategory,
                        subcategories[index] ?? null,
                ])
            }
        });

        return mainResponse;
    },

    getLocations: async filters => {
        const filtersUrlParams = filtersToQuery(filters);

        let ENDPOINT = LOCATIONS;
        if (window.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING) {
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

    getLocation: async locationId => {
        const response = await fetch(`${LOCATION}/${locationId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        return response.json();
    },

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

    getLanguages: () => fetch(LANGUAGES).then(response => response.json()),

    getSearchAddress: search => {
        const params = {
            format: 'json',
            limit: 5,
            q: search,
            'accept-language': window.APP_LANG || 'pl',
        };

        const queryString = new URLSearchParams(params).toString();

        return fetch(`${SEARCH_ADDRESS}?${queryString}`).then(response => response.json());
    },
};
