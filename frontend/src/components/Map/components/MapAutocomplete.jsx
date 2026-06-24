import React from 'react';
import styled from 'styled-components';
import { useMap } from 'react-leaflet';
import Autocomplete from '../../common/Autocomplete';

/**
 * Map autocomplete search component that allows users to search for locations.
 * When a location is selected, the map flies to that location with zoom level 13.
 * Positioned in the top-left corner of the map with responsive width.
 *
 * @returns {React.ReactElement} Autocomplete component wrapped in a positioned container
 */
const MapAutocomplete = () => {
    const map = useMap();

    const onPick = pick => {
        if (!pick || typeof pick.lat !== 'number' || typeof pick.lon !== 'number') {
            console.warn('Invalid pick coordinates:', pick);
            return;
        }
        map.flyTo([pick.lat, pick.lon], 13);
    };

    return (
        <Wrapper>
            <Autocomplete onClick={onPick} />
        </Wrapper>
    );
};

/**
 * Styled wrapper container for the autocomplete component.
 * Positioned absolutely in the top-left corner with responsive width.
 * Ensures autocomplete appears above map controls with high z-index.
 */
const Wrapper = styled.div`
    position: absolute;
    width: 300px;
    top: 10px;
    left: 10px;
    z-index: 9999999;
    @media only screen and (max-width: 768px) {
        width: 200px;
    }
`;

export default MapAutocomplete;
