import React from 'react';
import { render, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FiltersForm from '../src/components/FiltersForm/FiltersForm';
import SuggestNewPointButton from '../src/components/Map/components/SuggestNewPointButton';
import { LocationProvider } from '../src/components/Map/context/LocationContext';
import AppProviders from './utils/providers';
import { useDeploymentData } from '../src/context/DeploymentDataContext';
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

// A probe is the only way to see what the provider hands consumers, rather than what
// one particular consumer happens to render from it.
const SchemaProbe = () => {
    const { locationSchema, schemaError } = useDeploymentData();
    return (
        <div>
            <span data-testid="schema">{locationSchema === null ? 'null' : 'resolved'}</span>
            <span data-testid="error">{String(schemaError)}</span>
        </div>
    );
};

// A failed request must not be handed on as a schema: consumers would read an empty one
// as a real answer and build a form with no fields from it.
test('a failed schema request is not exposed as a resolved schema', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    httpService.getCategoriesData.mockResolvedValue({ categories: [], defaultChecked: {} });
    httpService.getLocationSchema.mockRejectedValue(new Error('schema unavailable'));

    const { getByTestId } = render(
        <AppProviders>
            <SchemaProbe />
        </AppProviders>,
    );

    await waitFor(() => expect(getByTestId('error')).toHaveTextContent('true'));
    expect(getByTestId('schema')).toHaveTextContent('null');

    consoleErrorSpy.mockRestore();
});
