import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { MapContainer } from 'react-leaflet';
import { MarkerPopup } from '../../src/components/MarkerPopup/MarkerPopup';
import { httpService } from '../../src/services/http/httpService';

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
        jest.spyOn(global, 'fetch').mockResolvedValue({
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
        global.fetch.mockRestore();
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
});
