import React from 'react';
import { render, act, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import { MapComponent } from '../../src/components/Map/MapComponent';
import { FiltersForm } from '../../src/components/FiltersForm/FiltersForm';
import { CategoriesProvider } from '../../src/components/Categories/CategoriesContext';
import { httpService } from '../../src/services/http/httpService';

jest.mock('../../src/services/http/httpService');

const categories = [
    [
        ['types', 'typy'],
        [
            ['clothes', 'ciuchy'],
            ['shoes', 'buty'],
        ],
    ],
];

const locations = [
    {
        uuid: '1',
        name: 'name',
        position: [50, 50],
    },
];

httpService.getLocations.mockResolvedValue(locations);
httpService.getCategoriesData.mockResolvedValue(categories);

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
        return act(() =>
            render(
                <CategoriesProvider>
                    <MapComponent />
                </CategoriesProvider>,
            ),
        );
    });

    it('renders without crashing', () => {
        expect(screen.getAllByRole('presentation').length).toBeGreaterThan(0);
    });

    it('does not fetch locations before filter state is initialized', () => {
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

        await act(async () => {
            render(
                <CategoriesProvider>
                    <FiltersForm />
                    <MapComponent />
                </CategoriesProvider>,
            );
        });

        expect(httpService.getLocations).toHaveBeenCalledTimes(1);
        expect(httpService.getLocations).toHaveBeenCalledWith({ types: ['shoes'] });
    });
});
