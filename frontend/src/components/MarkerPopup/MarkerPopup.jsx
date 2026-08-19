import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Marker } from 'react-leaflet';
import { isMobile } from 'react-device-detect';
import { Icon } from 'leaflet';
import { useTranslation } from 'react-i18next';
import httpService from '../../services/http/httpService';
import useMapStore from '../Map/store/map.store';

import LocationDetailsBox from './LocationDetails';
import MobilePopup from './MobilePopup';
import DesktopPopup from './DesktopPopup';
import getTypedMarkerIcon from './getTypedMarkerIcon';
import iconAsterisk from '../../res/img/marker-icon-asterisk.png';

/**
 * Wrapper component that fetches full location details and renders them in a popup.
 * Automatically selects between mobile and desktop popup layouts based on device type.
 *
 * @param {Object} props - Component props
 * @param {Object} props.theplace - Basic place object containing at minimum a uuid
 * @param {string} props.theplace.uuid - Unique identifier for the location
 * @returns {React.ReactElement} Popup component with location details or loading state
 */
const LocationDetailsBoxWrapper = ({ theplace }) => {
    const { t } = useTranslation();
    const [place, setPlace] = useState(null);
    const ChosenPopup = isMobile ? MobilePopup : DesktopPopup;

    useEffect(() => {
        let isMounted = true;

        const fetchPlace = async () => {
            try {
                const fetchedPlace = await httpService.getLocation(theplace.uuid);
                if (isMounted) {
                    setPlace(fetchedPlace);
                }
            } catch (error) {
                if (isMounted) {
                    console.error('Failed to fetch location:', error);
                    setPlace({ error: true });
                }
            }
        };

        fetchPlace();

        return () => {
            isMounted = false;
        };
    }, [theplace.uuid]);

    const renderContent = () => {
        if (place?.error) {
            return <p>{t('loadLocationError')}</p>;
        }
        if (place) {
            return <LocationDetailsBox place={place} />;
        }
        return <p>{t('loading')}</p>;
    };

    return <ChosenPopup>{renderContent()}</ChosenPopup>;
};

LocationDetailsBoxWrapper.propTypes = {
    theplace: PropTypes.shape({
        uuid: PropTypes.string.isRequired,
    }).isRequired,
};

/**
 * Custom Leaflet icon for markers with remarks/special annotations.
 * Displays an asterisk icon to visually distinguish remarked locations from standard markers.
 */
const asteriskIcon = new Icon({
    iconUrl: iconAsterisk,
    iconSize: [40, 48], // size of the icon
    iconAnchor: [19, 46], // point of the icon which will correspond to marker's location
    popupAnchor: [0, -40], // point from which the popup should open relative to the iconAnchor
});

/**
 * Interactive map marker component that displays location details in a popup when clicked.
 * Supports special visual indication for locations with remarks using an asterisk icon.
 *
 * @param {Object} props - Component props
 * @param {Object} props.place - Location data object
 * @param {number[]} props.place.position - Coordinates [latitude, longitude]
 * @param {boolean} [props.place.has_remark] - Whether this location has a remark (uses asterisk icon if true)
 * @returns {React.ReactElement} Leaflet Marker component with click-to-show-details functionality
 */
const MarkerPopup = ({ place }) => {
    const selectedLocationId = useMapStore(state => state.selectedLocationId);
    const setSelectedLocationId = useMapStore(state => state.setSelectedLocationId);
    const [isClicked, setIsClicked] = useState(false);

    // TODO: this only opens the popup if `place`'s Marker is actually attached to
    // the map. Leaflet.markercluster detaches individual markers while they sit
    // inside an unexpanded cluster bubble, so a shared ?locationId= link to a
    // clustered location silently fails to open its popup on desktop (mobile's
    // MobilePopup is unaffected - it's a state-driven MUI Dialog, not tied to the
    // Leaflet marker). Fix: call the cluster group's zoomToShowLayer(marker, cb)
    // before/instead of setIsClicked when the marker is clustered. Covered by the
    // xfail'd test_shared_link_opens_popup_with_correct_content in e2e-tests.
    useEffect(() => {
        if (selectedLocationId === place.uuid) {
            setIsClicked(true);
            setSelectedLocationId(null);
        }
    }, [selectedLocationId, place.uuid, setSelectedLocationId]);

    const handleMarkerClick = () => {
        setIsClicked(true);
    };

    const markerProps = {
        position: place.position,
        eventHandlers: {
            click: handleMarkerClick,
        },
        alt: place.has_remark ? 'Marker-Asterisk' : 'Marker',
    };

    // Prefer a marker_styles match (getTypedMarkerIcon adds an asterisk badge to
    // it when place.has_remark is set, so a remarked location keeps its type/color
    // styling) and only fall back to the plain asterisk icon when there's no
    // match to style - e.g. a legacy/unconfigured deployment. Only add an icon
    // prop when we actually have a custom icon: passing icon={undefined} causes
    // errors in MarkerClusterGroup during cluster zoom animations.
    const typedIcon = getTypedMarkerIcon(place);
    if (typedIcon) {
        markerProps.icon = typedIcon;
    } else if (place.has_remark) {
        markerProps.icon = asteriskIcon;
    }

    return (
        // eslint-disable-next-line react/jsx-props-no-spreading -- icon is only conditionally set
        <Marker {...markerProps}>
            {isClicked && <LocationDetailsBoxWrapper theplace={place} />}
        </Marker>
    );
};

MarkerPopup.propTypes = {
    place: PropTypes.shape({
        position: PropTypes.arrayOf(PropTypes.number).isRequired,
        has_remark: PropTypes.bool, // eslint-disable-line camelcase -- matches backend API schema property name
        uuid: PropTypes.string.isRequired,
    }).isRequired,
};

export default MarkerPopup;
