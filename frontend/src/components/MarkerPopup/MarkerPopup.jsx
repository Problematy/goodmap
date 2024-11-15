import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Marker, Popup, useMap } from 'react-leaflet';
import { isMobile } from 'react-device-detect';

import { MarkerContent } from './MarkerContent';
import { MobilePopup } from './MobilePopup';

const MobileMarker = ({ place }) => {
    const [open, setOpen] = useState(false);
    const map = useMap();

    const handleClickOpen = () => {
        const offset = 0.003;
        const newLat = place.position[0] - offset;
        map.panTo([newLat, place.position[1]], { duration: 0.5 });
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    return (
        <Marker
            position={place.position}
            key={place.metadata.UUID}
            eventHandlers={{ click: handleClickOpen }}
        >
            <MobilePopup isOpen={open} onCloseHandler={handleClose}>
                <MarkerContent place={place} isMobileVariable={true} />
            </MobilePopup>
        </Marker>
    );
};

const DesktopMarker = ({ place }) => {
    return (
        <Marker position={place.position} key={place.metadata.UUID}>
            <Popup>
                <MarkerContent place={place} isMobileVariable={false} />
            </Popup>
        </Marker>
    );
};

// TODO Rename MarkerPopup because it is not a popup for mobile

// Maybe ResponsiveMarker? The filename should be changed too.
export const MarkerPopup = ({ place }) => {
    if (isMobile) return <MobileMarker place={place} />;
    else return <DesktopMarker place={place} />;
};

MarkerPopup.propTypes = {
    place: PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtitle: PropTypes.string.isRequired,
        data: PropTypes.shape({}).isRequired,
    }).isRequired,
};
