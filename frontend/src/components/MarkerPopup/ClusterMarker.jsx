import PropTypes from 'prop-types';
import React from 'react';
import { Marker } from '@adamscybot/react-leaflet-component-marker';
import styled from 'styled-components';
import { useMap } from 'react-leaflet';

export const ClusterMarker = ({ cluster }) => {
    const map = useMap();
    const handleClusterClick = () => {
        map.flyTo(cluster.position, map.getZoom() + 5);
    };

    return (
        <Marker
            position={cluster.position}
            eventHandlers={{
                click: handleClusterClick,
            }}
            icon={<ClusterMarkerIcon cluster={cluster} />}
        />
    );
};

const ClusterMarkerIcon = ({ cluster }) => {
    return (
        <ClusterMarkerContainer>
            <span>{cluster.cluster_count}</span>
        </ClusterMarkerContainer>
    );
};

const ClusterMarkerContainer = styled.div`
    width: 30px;
    height: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #007bff;
    color: white;
    border-radius: 50%;
`;

ClusterMarkerIcon.propTypes = {
    cluster: PropTypes.shape({
        cluster_count: PropTypes.number.isRequired,
    }).isRequired,
};

ClusterMarker.propTypes = {
    cluster: PropTypes.shape({
        position: PropTypes.arrayOf(PropTypes.number).isRequired,
        cluster_count: PropTypes.number.isRequired,
    }).isRequired,
};
