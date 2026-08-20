import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { MapContainer } from 'react-leaflet';
import MarkerPopup from '../../src/components/MarkerPopup/MarkerPopup';
import httpService from '../../src/services/http/httpService';
import useMarkerStylesStore from '../../src/components/Map/store/markerStyles.store';

jest.mock('../../src/services/http/httpService');

const location = {
    position: [51.1095, 17.0525],
    uuid: '21231',
    has_remark: false, // eslint-disable-line camelcase -- matches backend API schema property name
};

const locationData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: [
        ['length', 112.5],
        ['accessible_by', ['pedestrians', 'cars']],
        [
            'CTA',
            {
                type: 'CTA',
                value: 'https://www.example.com',
                displayValue: 'Visit example.org!',
            },
        ],
    ],
    metadata: {
        uuid: '21231',
    },
};

httpService.getLocation.mockResolvedValue(locationData);
// Every mount now fires a lazy marker-styles request (see requestMarkerStyle.js) -
// a harmless default so it always resolves, even in tests that don't care about it.
httpService.getMarkerStyles.mockResolvedValue({});

/**
 * requestMarkerStyle.js debounces/batches uuids through module-level state shared
 * by every test in this file. Describes below that render with real timers must
 * drain that debounce window before finishing, or its still-pending timer fires
 * during a later (fake-timer) describe and merges its uuid into that batch.
 */
const flushMarkerStyleDebounce = () =>
    act(
        () =>
            new Promise(resolve => {
                setTimeout(resolve, 200);
            }),
    );

describe('MarkerPopup', () => {
    beforeEach(() => {
        jest.spyOn(globalThis, 'fetch').mockResolvedValue({
            json: jest.fn().mockResolvedValue(locationData),
        });
        return act(() =>
            render(
                <MapContainer
                    center={[51.1095, 17.0525]}
                    zoom={10}
                    style={{ height: '100vh', width: '100%' }}
                >
                    <MarkerPopup place={location} key={location.uuid} />
                </MapContainer>,
            ),
        );
    });

    afterEach(async () => {
        globalThis.fetch.mockRestore();
        await flushMarkerStyleDebounce();
    });

    it('should render marker without popup', () => {
        expect(screen.getByAltText(/marker/i)).toBeInTheDocument();
        expect(document.querySelector('.leaflet-popup')).not.toBeInTheDocument();
        expect(screen.queryByText(locationData.title)).not.toBeInTheDocument();
    });

    it('should render marker popup after click on marker', () => {
        const marker = screen.getByAltText(/marker/i);
        fireEvent.click(marker);
        return waitFor(() => {
            expect(document.querySelector('.leaflet-popup')).toBeInTheDocument();
            expect(screen.queryByText(locationData.title)).toBeInTheDocument();
        });
    });

    it('should use default alt text when remark is false', () => {
        const marker = screen.getByAltText('Marker');
        expect(marker).toBeInTheDocument();
        expect(screen.queryByAltText('Marker-Asterisk')).not.toBeInTheDocument();
    });

    it('should not pass icon prop when remark is false to prevent MarkerClusterGroup issues', () => {
        const marker = screen.getByAltText(/Marker/i);
        const leafletMarker = marker.closest('.leaflet-marker-icon');

        // When remark is false, the marker should use Leaflet's default icon
        // This is important because passing icon={undefined} causes errors in MarkerClusterGroup
        // during cluster zoom animations
        expect(leafletMarker).toBeInTheDocument();

        // Verify default Leaflet icon dimensions (25x41) are used, not custom asterisk icon (40x48)
        const style = window.getComputedStyle(leafletMarker);
        expect(style.width).not.toBe('40px'); // Should NOT have asterisk icon width
    });
});

describe('MarkerPopup with remark', () => {
    beforeEach(() => {
        jest.spyOn(globalThis, 'fetch').mockResolvedValue({
            json: jest.fn().mockResolvedValue(locationData),
        });
    });

    afterEach(async () => {
        globalThis.fetch.mockRestore();
        await flushMarkerStyleDebounce();
    });

    it('should render our own pin with an asterisk badge when remark is true', () => {
        // eslint-disable-next-line camelcase -- matches backend API schema property name
        const locationWhenRemarkIsTrue = { ...location, has_remark: true };
        act(() => {
            render(
                <MapContainer
                    center={locationWhenRemarkIsTrue.position}
                    zoom={10}
                    style={{ height: '100vh', width: '100%' }}
                >
                    <MarkerPopup
                        place={locationWhenRemarkIsTrue}
                        key={locationWhenRemarkIsTrue.uuid}
                    />
                </MapContainer>,
            );
        });
        const marker = document.querySelector('.custom-typed-marker-icon');
        expect(marker).toBeInTheDocument();
        expect(marker.querySelector('span')).toHaveTextContent('*');
    });

    it('should pass custom icon prop when remark is true', () => {
        // eslint-disable-next-line camelcase -- matches backend API schema property name
        const locationWithRemark = { ...location, has_remark: true };
        act(() => {
            render(
                <MapContainer
                    center={locationWithRemark.position}
                    zoom={10}
                    style={{ height: '100vh', width: '100%' }}
                >
                    <MarkerPopup place={locationWithRemark} key={locationWithRemark.uuid} />
                </MapContainer>,
            );
        });

        const marker = document.querySelector('.custom-typed-marker-icon');

        // When remark is true, marker should have our own pin, not Leaflet's default icon
        expect(marker).toBeInTheDocument();

        // Verify our pin's dimensions (45x50) are applied, not Leaflet's default (25x41)
        const style = window.getComputedStyle(marker);
        expect(style.width).toBe('45px');
        expect(style.height).toBe('50px');
    });
});

describe('MarkerPopup lazy marker styling', () => {
    // A uuid distinct from `location`'s (used by the describes above, which run with
    // real timers) so a leftover real setTimeout from those can't resolve into this
    // describe's store state mid-test and make "already known" skip our own request.
    const lazyLocation = {
        position: [51.2, 17.1],
        uuid: 'lazy-marker-styling-uuid',
        has_remark: false, // eslint-disable-line camelcase -- matches backend API schema property name
    };

    beforeEach(() => {
        jest.useFakeTimers();
        useMarkerStylesStore.setState({ stylesByUuid: {} });
        globalThis.MARKER_STYLES = {
            icon_field: 'pointType', // eslint-disable-line camelcase -- matches backend API schema property name
            icons: { parcelLocker: 'https://cdn.example.com/parcel-locker.svg' },
        };
        httpService.getMarkerStyles.mockResolvedValue({
            [lazyLocation.uuid]: { pointType: 'parcelLocker' },
        });
    });

    afterEach(() => {
        jest.useRealTimers();
        delete globalThis.MARKER_STYLES;
    });

    it('fetches marker styling once the marker becomes individually visible', async () => {
        await act(async () => {
            render(
                <MapContainer
                    center={lazyLocation.position}
                    zoom={10}
                    style={{ height: '100vh', width: '100%' }}
                >
                    <MarkerPopup place={lazyLocation} key={lazyLocation.uuid} />
                </MapContainer>,
            );
        });

        expect(httpService.getMarkerStyles).not.toHaveBeenCalledWith([lazyLocation.uuid]);

        await act(async () => {
            jest.advanceTimersByTime(200);
            await Promise.resolve();
        });

        expect(httpService.getMarkerStyles).toHaveBeenCalledWith([lazyLocation.uuid]);
    });

    it('re-renders the marker with the lazily-fetched icon once it arrives', async () => {
        await act(async () => {
            render(
                <MapContainer
                    center={lazyLocation.position}
                    zoom={10}
                    style={{ height: '100vh', width: '100%' }}
                >
                    <MarkerPopup place={lazyLocation} key={lazyLocation.uuid} />
                </MapContainer>,
            );
        });

        // Nothing matched yet - default Leaflet icon, no custom pin
        expect(document.querySelector('.custom-typed-marker-icon')).not.toBeInTheDocument();

        await act(async () => {
            jest.advanceTimersByTime(200);
            await Promise.resolve();
        });

        const marker = document.querySelector('.custom-typed-marker-icon');
        expect(marker).toBeInTheDocument();
        expect(marker.innerHTML).toContain('https://cdn.example.com/parcel-locker.svg');
    });
});
