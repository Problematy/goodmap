import React from 'react';
import styled from 'styled-components';
import { useMap } from 'react-leaflet';
import Autocomplete from '../../common/Autocomplete';

const MapAutocomplete = () => {
    const map = useMap();

    const onPick = pick => {
        map.flyTo([pick.lat, pick.lon], 13);
    };

    return (
        <Wrapper>
            <Autocomplete onClick={onPick} />
        </Wrapper>
    );
};

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
