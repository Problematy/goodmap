import { CATEGORIES, CATEGORY, DATA, LANGUAGES, LOCATION, LOCATIONS, SEARCH_ADDRESS, LOCATIONS_CLUSTERED } from './endpoints';
import { useMapStore } from '../../components/Map/store/map.store';

function filtersToQuery(filters) {
    const basicQuery = Object.entries(filters)
        .map(([key, values]) => values.map(value => `${key}=${value}`).join('&'))
        .join('&');

    if (window.USE_SERVER_SIDE_CLUSTERING) {
        const mapConfigurationData = useMapStore.getState().mapConfiguration;
        if (mapConfigurationData) {
            const mapConfigQueryString = Object.entries(mapConfigurationData)
                .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
                .join('&');
            return `${basicQuery}&${mapConfigQueryString}`;
        }
    }
    return basicQuery;
}

 export const httpService = {
    getCategories: () => fetch(CATEGORIES).then(response => response.json()),

    getSubcategories: category =>
        fetch(`${CATEGORY}/${category}`).then(response => response.json()),

    getCategoriesData: async () => {
        const categories = await httpService.getCategories();
        const subcategoriesPromises = categories.map(([categoryName, _translation]) =>
            httpService.getSubcategories(categoryName),
        );
        const subcategoriesResponse = Promise.all(subcategoriesPromises);

        return subcategoriesResponse.then(subcategories =>
            categories.map((subcategory, index) => [subcategory, subcategories[index]]),
        );
    },

    getLocations: async filters => {
      let ENDPOINT = DATA;  // TODO remove DATA endpont after removing it from main API
      const filtersUrlParams = filtersToQuery(filters);
      if (window.USE_SERVER_SIDE_CLUSTERING) {
          ENDPOINT = LOCATIONS_CLUSTERED;
      } else if (window.USE_LAZY_LOADING) {
          ENDPOINT = LOCATIONS;
      }


      const response = await fetch(`${ENDPOINT}?${filtersUrlParams}`, {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json',
          },
      });
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

    getLocationsWithLatLon: async (lat, lon, filters) => {
        const query = filtersToQuery(filters);
        const response = await fetch(`${DATA}?${query}&lat=${lat}&lon=${lon}&limit=10`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        return response.json();
    },

    getLanguages: () => fetch(LANGUAGES).then(response => response.json()),

    getSearchAddress: (search) => {
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
