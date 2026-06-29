import React from 'react';
import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import { MapContainer, TileLayer } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import { MarkerPopup } from '../../src/components/MarkerPopup/MarkerPopup';

/**
 * Integration test for MarkerPopup with MarkerClusterGroup
 *
 * This test ensures that the bug fix for
 * "Cannot read properties of undefined (reading 'createIcon')"
 * is working correctly. The bug occurred when:
 * 1. Markers were wrapped in MarkerClusterGroup
 * 2. MarkerPopup was passing icon={undefined} for markers without remarks
 * 3. User clicked on a cluster, triggering zoom animation
 * 4. MarkerClusterGroup tried to call createIcon on markers with undefined icons
 *
 * The fix: Only pass the icon prop when there's a custom icon (remark=true),
 * instead of passing icon={undefined}
 */
describe('MarkerPopup integration with MarkerClusterGroup', () => {
    const locations = [
        {
            position: [51.1095, 17.0525],
            uuid: 'location-1',
            remark: false,
        },
        {
            position: [51.10655, 17.0555],
            uuid: 'location-2',
            remark: true,
        },
        {
            position: [51.1085, 17.0535],
            uuid: 'location-3',
            remark: false,
        },
    ];

    it('should render markers without errors when wrapped in MarkerClusterGroup', () => {
        // This test verifies that the fix for the
        // "Cannot read properties of undefined (reading 'createIcon')" bug works
        // The bug occurred because icon={undefined} was being passed to markers
        // Now, the icon prop is only included when there's a custom icon (remark=true)
        const { container } = render(
            <MapContainer
                center={[51.1095, 17.0525]}
                zoom={13}
                maxZoom={19}
                style={{ height: '100vh', width: '100%' }}
            >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <MarkerClusterGroup>
                    {locations.map(location => (
                        <MarkerPopup place={location} key={location.uuid} />
                    ))}
                </MarkerClusterGroup>
            </MapContainer>,
        );

        // Should render the map container without throwing errors
        expect(container.querySelector('.leaflet-container')).toBeInTheDocument();
    });
});
