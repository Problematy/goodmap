import { CATEGORIES, CATEGORY, DATA, LANGUAGES, LOCATION, LOCATIONS, SEARCH_ADDRESS } from './endpoints';

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

    getLocations: async filtersUrlParams => {
      const ENDPOINT = window.USE_LAZY_LOADING ? LOCATIONS : DATA;
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

    getLocationsWithLatLon: async (lat, lon, allCheckboxes) => {
        const filtersUrlParams = allCheckboxes.filter(n => n).join('&');
        const response = await fetch(`${DATA}?${filtersUrlParams}&lat=${lat}&lon=${lon}&limit=10`, {
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
