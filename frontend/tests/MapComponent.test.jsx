import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import { MapComponent } from '../src/components/Map/MapComponent';
import { Marker, Popup } from 'react-leaflet';

describe('MapComponent', () => {
    const mockMarkers = [
        <Marker position={[51.10655, 17.0555]} key="1">
            <Popup>
                <div>
                    <h3>Zwierzyniecka</h3>
                    <p>small bridge</p>
                    <p>Accessible by: bikes, pedestrians</p>
                </div>
            </Popup>
        </Marker>,
        <Marker position={[51.10675, 17.0575]} key="2">
            <Popup>
                <div>
                    <h3>Grunwaldzki</h3>
                    <p>big bridge</p>
                    <p>Accessible by: bikes, pedestrians, cars</p>
                </div>
            </Popup>
        </Marker>,
    ];

    it('renders without crashing', () => {
        render(<MapComponent markers={mockMarkers} />);
        expect(screen.getAllByRole('presentation').length).toBeGreaterThan(0);
    });

    it('does not render markers if none are provided', () => {
        render(<MapComponent markers={[]} />);
        const markers = screen.queryAllByRole('marker');
        expect(markers).toHaveLength(0);
    });
});
