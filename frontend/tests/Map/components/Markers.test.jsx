import React from 'react';
import '@testing-library/jest-dom';
import { render, waitFor } from '@testing-library/react';
import { MapContainer } from 'react-leaflet';
import { Markers } from '../../../src/components/Map/components/Markers';
import { CategoriesProvider } from '../../../src/components/Categories/CategoriesContext';
import { httpService } from '../../../src/services/http/httpService';

jest.mock('../../../src/services/http/httpService', () => ({
    httpService: {
        getCategoriesData: jest.fn(),
        getLocations: jest.fn(),
    },
}));

const renderMarkers = onLoadingChange =>
    render(
        <CategoriesProvider>
            <MapContainer center={[51.1, 17.03]} zoom={13} maxZoom={19} style={{ height: '100vh' }}>
                <Markers onLoadingChange={onLoadingChange} />
            </MapContainer>
        </CategoriesProvider>,
    );

beforeEach(() => {
    httpService.getCategoriesData.mockResolvedValue({ categories: [], defaultChecked: {} });
    // Server-side clustering settles the loading state directly, rather than waiting on
    // a Leaflet cluster event, which keeps these assertions about Markers itself.
    globalThis.FEATURE_FLAGS = { USE_SERVER_SIDE_CLUSTERING: true };
});

afterEach(() => {
    delete globalThis.FEATURE_FLAGS;
});

describe('Markers', () => {
    it('reports loading finished once locations arrive', async () => {
        httpService.getLocations.mockResolvedValue([]);
        const onLoadingChange = jest.fn();

        renderMarkers(onLoadingChange);

        await waitFor(() => expect(onLoadingChange).toHaveBeenLastCalledWith(false));
    });

    it('settles the loading state when the locations request is rejected', async () => {
        // getLocations rejects on a non-2xx response. Without a failure path the map
        // would sit in its loading state forever, with the rejection unhandled.
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        httpService.getLocations.mockRejectedValue(new Error('HTTP 400'));
        const onLoadingChange = jest.fn();

        renderMarkers(onLoadingChange);

        await waitFor(() => expect(onLoadingChange).toHaveBeenLastCalledWith(false));
        expect(consoleErrorSpy).toHaveBeenCalledWith(
            'Failed to load locations:',
            expect.any(Error),
        );
        consoleErrorSpy.mockRestore();
    });
});
