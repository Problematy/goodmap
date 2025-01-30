import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Marker } from 'react-leaflet';
import { isMobile } from 'react-device-detect';
import { httpService } from '../../services/http/httpService';

import { LocationDetailsBox } from './LocationDetails';
import { MobilePopup } from './MobilePopup';
import { DesktopPopup } from './DesktopPopup';

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
            const fetchedPlace = await httpService.getLocation(theplace.uuid);
            setPlace(fetchedPlace);
        };
        fetchPlace();
    }, [theplace.uuid]);

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
