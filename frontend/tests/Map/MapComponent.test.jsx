import React from 'react';
import { render, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import MapComponent from '../../src/components/Map/MapComponent';
import FiltersForm from '../../src/components/FiltersForm/FiltersForm';
import AppProviders from '../utils/providers';
import httpService from '../../src/services/http/httpService';

jest.mock('../../src/services/http/httpService');

const categories = [
    {
        categoryKey: 'types',
        categoryName: 'typy',
        options: [
            ['clothes', 'ciuchy'],
            ['shoes', 'buty'],
        ],
        categoriesHelp: [],
        optionsHelp: [],
        filterMode: 'or',
    },
];

const locations = [
    {
        uuid: '1',
        name: 'name',
        position: [50, 50],
    },
];

httpService.getLocations.mockResolvedValue(locations);
httpService.getCategoriesData.mockResolvedValue({ categories, defaultChecked: {} });
// Fetched by the provider alongside the categories; no component here reads it.
httpService.getLocationSchema.mockResolvedValue({});

describe('MapComponent', () => {
    beforeAll(() => {
        globalThis.FEATURE_FLAGS = {
            CATEGORIES_HELP: true,
        };
    });

    beforeEach(() => {
        jest.spyOn(globalThis, 'fetch').mockResolvedValue({
            json: jest.fn().mockResolvedValue(categories),
        });
    });

    it('renders without crashing', async () => {
        render(
            <AppProviders>
                <MapComponent />
            </AppProviders>,
        );

        await waitFor(() => expect(screen.getAllByRole('presentation').length).toBeGreaterThan(0));
    });

    // eslint-disable-next-line es-x/no-async-functions -- needed to await waitFor
    it('does not fetch locations before filter state is initialized', async () => {
        httpService.getLocations.mockClear();
        // Never resolves, so the provider leaves the filter state uninitialized.
        httpService.getCategoriesData.mockReturnValueOnce(new Promise(() => {}));

        render(
            <AppProviders>
                <MapComponent />
            </AppProviders>,
        );

        // Let the provider's other fetch settle first, so this asserts on the filter
        // state rather than on merely having run before anything could happen.
        await waitFor(() => expect(httpService.getLocationSchema).toHaveBeenCalled());
        expect(httpService.getLocations).not.toHaveBeenCalled();
    });
});

describe('MapComponent with FiltersForm', () => {
    beforeAll(() => {
        globalThis.FEATURE_FLAGS = {};
    });

    it('fetches locations once, already filtered by default-checked options', async () => {
        httpService.getLocations.mockClear();
        httpService.getCategoriesData.mockResolvedValueOnce({
            categories,
            defaultChecked: { types: ['shoes'] },
        });

        render(
            <AppProviders>
                <FiltersForm />
                <MapComponent />
            </AppProviders>,
        );

        await waitFor(() => expect(httpService.getLocations).toHaveBeenCalledTimes(1));
        expect(httpService.getLocations).toHaveBeenCalledWith({ types: ['shoes'] });
    });
});
