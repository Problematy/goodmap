import { CATEGORIES, CATEGORY, DATA, LANGUAGES } from './endpoints';

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
        const response = await fetch(`${DATA}?${filtersUrlParams}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        return response.json();
    },

    getLanguages: () => fetch(LANGUAGES).then(response => response.json()),
};
