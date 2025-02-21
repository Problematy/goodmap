import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { MapContainer } from 'react-leaflet';
import { ClusterMarker } from '../../src/components/MarkerPopup/ClusterMarker';

const correctClusterData = {
    position: [51.1095, 17.0525],
    cluster_count: 5, // eslint-disable-line camelcase
};

describe('ClusterMarker', () => {
    beforeEach(() => {
        render(
            <MapContainer
                center={[51.1095, 17.0525]}
                zoom={10}
                style={{ height: '100vh', width: '100%' }}
            >
                <ClusterMarker cluster={correctClusterData} />
            </MapContainer>,
        );
    });

    it('should render cluster count', () => {
        expect(screen.getByText(correctClusterData.cluster_count)).toBeInTheDocument();
    });
});
