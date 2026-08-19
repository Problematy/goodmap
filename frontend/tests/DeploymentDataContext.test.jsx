import React from 'react';
import { render, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FiltersForm from '../src/components/FiltersForm/FiltersForm';
import SuggestNewPointButton from '../src/components/Map/components/SuggestNewPointButton';
import { LocationProvider } from '../src/components/Map/context/LocationContext';
import AppProviders from './utils/providers';
import httpService from '../src/services/http/httpService';

jest.mock('axios');
jest.mock('../src/services/http/httpService', () => ({
    __esModule: true,
    default: {
        getCategoriesData: jest.fn(),
        getLocations: jest.fn(),
        getLocationSchema: jest.fn(),
    },
}));
jest.mock('../src/utils/toast', () => ({
    __esModule: true,
    default: { success: jest.fn(), error: jest.fn() },
}));
jest.mock('browser-image-compression');

// Both the filter panel and the suggestion dialog need the category definitions.
// The provider owns the fetch so they share one request instead of making two.
test('categories are fetched once for all consumers', async () => {
    httpService.getCategoriesData.mockResolvedValue({ categories: [], defaultChecked: {} });
    httpService.getLocationSchema.mockResolvedValue({});

    render(
        <AppProviders>
            <LocationProvider>
                <FiltersForm />
                <SuggestNewPointButton />
            </LocationProvider>
        </AppProviders>,
    );

    await waitFor(() => expect(httpService.getCategoriesData).toHaveBeenCalled());
    expect(httpService.getCategoriesData).toHaveBeenCalledTimes(1);
});
