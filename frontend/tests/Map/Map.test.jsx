import React from 'react';
import '@testing-library/jest-dom';
import { act } from '@testing-library/react';
import MapContainer from '../../src/components/Map/Map';

jest.mock('../../src/components/Map/MapComponent', () => () => <div data-testid="map-component" />);
jest.mock('../../src/components/FiltersForm/FiltersForm', () => () => (
    <div data-testid="filters-form" />
));
jest.mock('../../src/components/common/AppToaster', () => () => null);
jest.mock('../../src/services/http/httpService', () => ({
    __esModule: true,
    default: {
        getCategoriesData: jest.fn().mockResolvedValue({ categories: [], defaultChecked: {} }),
        getLocationSchema: jest.fn().mockResolvedValue({}),
    },
}));

// Map.jsx creates its own React root instead of being rendered by a test renderer,
// so act() has to be told this is an act environment.
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const renderApp = async () => {
    await act(async () => {
        MapContainer();
    });
};

describe('MapWrap placeholders', () => {
    let error;

    // PropTypes' `node` validator does not recognise portals, so every render here
    // warns about FiltersProvider's children (a pre-existing dev-only warning, not
    // something these tests are about). console.error is silenced and asserted on by
    // message instead of by call count.
    beforeEach(() => {
        error = jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        document.body.innerHTML = '';
        jest.restoreAllMocks();
    });

    it('renders both portals when the left panel is present', async () => {
        document.body.innerHTML = '<div id="map"></div><div id="filter-form"></div>';

        await renderApp();

        expect(document.querySelector('[data-testid="map-component"]')).not.toBeNull();
        expect(document.querySelector('[data-testid="filters-form"]')).not.toBeNull();
    });

    // A deployment with no categories renders no left panel at all, so #filter-form is
    // legitimately missing - the map must still come up rather than the whole app
    // bailing out.
    it('still renders the map when the filters placeholder is missing', async () => {
        document.body.innerHTML = '<div id="map"></div>';
        await renderApp();

        expect(document.querySelector('[data-testid="map-component"]')).not.toBeNull();
        expect(document.querySelector('[data-testid="filters-form"]')).toBeNull();
        expect(error).not.toHaveBeenCalledWith(expect.stringContaining('render the map'));
    });

    it('renders nothing when the map placeholder is missing', async () => {
        document.body.innerHTML = '<div id="filter-form"></div>';
        await renderApp();

        expect(document.querySelector('[data-testid="map-component"]')).toBeNull();
        expect(document.querySelector('[data-testid="filters-form"]')).toBeNull();
        expect(error).toHaveBeenCalledWith(expect.stringContaining('render the map'));
    });
});
