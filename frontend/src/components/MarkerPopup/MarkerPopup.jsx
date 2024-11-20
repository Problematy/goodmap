import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Marker, Popup } from 'react-leaflet';
import { isMobile } from 'react-device-detect';
import { httpService } from '../../services/http/httpService';
import styled from 'styled-components';

import { LocationDetailsBox } from './LocationDetails';
import { MobilePopup } from './MobilePopup';

const StyledPopup = styled(Popup)`
    min-width: 300px;
`;

// DesktopPopup is a workaround for not existing lazy loading Popup as
// react-leaflet Popup doesn't support .open() function
const DesktopPopup = ({ children }) => {
    const popupRef = useRef(null);

    useEffect(() => {
        if (popupRef.current) {
            const marker = popupRef.current._source;
            if (marker) {
                marker.openPopup();
            }
        }
    }, []);

    return <StyledPopup ref={popupRef}>{children}</StyledPopup>;
};

const LocationDetailsBoxWrapper = ({ theplace }) => {
    const [place, setPlace] = useState(null);
    const ChosenPopup = isMobile ? MobilePopup : DesktopPopup;

    if (!window.USE_LAZY_LOADING) {
        return (
            <ChosenPopup>
                <LocationDetailsBox place={theplace} />
            </ChosenPopup>
        );
    }

    useEffect(() => {
        const fetchPlace = async () => {
            const fetchedPlace = await httpService.getLocation(theplace.UUID);
            setPlace(fetchedPlace);
        };
        fetchPlace();
    }, [theplace.UUID]);

    return (
        <ChosenPopup>
            {place ? <LocationDetailsBox place={place} /> : <p>Loading...</p>}
        </ChosenPopup>
    );
};

export const MarkerPopup = ({ place }) => {
    const [isClicked, setIsClicked] = useState(false);
    const handleMarkerClick = e => {
        setIsClicked(true);
    };
    return (
        <Marker
            position={place.position}
            eventHandlers={{
                click: handleMarkerClick,
            }}
        >
            {isClicked && <LocationDetailsBoxWrapper theplace={place} />}
        </Marker>
    );
};

MarkerPopup.propTypes = {
    place: PropTypes.shape({
        position: PropTypes.arrayOf(PropTypes.number).isRequired,
    }).isRequired,
};
