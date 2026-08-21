import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { MapContainer } from 'react-leaflet';
import { Marker as LeafletMarker } from 'leaflet';
import MarkerPopup from '../../src/components/MarkerPopup/MarkerPopup';
import httpService from '../../src/services/http/httpService';

jest.mock('../../src/services/http/httpService');

const location = {
    position: [51.1095, 17.0525],
    uuid: '21231',
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

    afterEach(() => {
        globalThis.fetch.mockRestore();
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

    afterEach(() => {
        globalThis.fetch.mockRestore();
    });

    it('should render our own pin with an asterisk badge when remark is true', () => {
        const locationWhenRemarkIsTrue = { ...location, marker: { badge: true } };
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
        const locationWithRemark = { ...location, marker: { badge: true } };
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

    it('does not rebuild the icon on a re-render that leaves place.marker alone', () => {
        // react-leaflet compares icon by identity (updateMarker in react-leaflet/lib/Marker.js),
        // so a fresh DivIcon per render re-runs setIcon - and with it renderToString and a
        // full rewrite of the pin - on every store write, for every marker on the map.
        const setIcon = jest.spyOn(LeafletMarker.prototype, 'setIcon');
        const locationWithRemark = { ...location, marker: { badge: true } };
        const tree = zoom => (
            <MapContainer
                center={locationWithRemark.position}
                zoom={zoom}
                style={{ height: '100vh', width: '100%' }}
            >
                <MarkerPopup place={locationWithRemark} key={locationWithRemark.uuid} />
            </MapContainer>
        );

        // render/rerender already flush their own updates, so no act() wrapper here.
        const { rerender } = render(tree(10));
        setIcon.mockClear();

        rerender(tree(11));

        try {
            expect(setIcon).not.toHaveBeenCalled();
        } finally {
            setIcon.mockRestore();
        }
    });
});
