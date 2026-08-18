import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { Popup } from 'react-leaflet';
import styled from 'styled-components';

/**
 * Styled Leaflet popup component with minimum width of 300px.
 */
const StyledPopup = styled(Popup)`
    min-width: 300px;
`;

/**
 * Desktop popup component for displaying location details.
 * Automatically opens the popup on mount using a ref to access the underlying Leaflet marker.
 * This is a workaround since react-leaflet's Popup doesn't support lazy loading or .open() function.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Content to display inside the popup
 * @returns {React.ReactElement} Styled Popup component that auto-opens on mount
 */
const DesktopPopup = ({ children }) => {
    const popupRef = useRef(null);

    useEffect(() => {
        if (popupRef.current) {
            // Leaflet's internal Marker reference - no public API exposes this.
            // eslint-disable-next-line no-underscore-dangle
            const marker = popupRef.current._source;
            if (marker) {
                marker.openPopup();
            }
        }
    }, []);

    return <StyledPopup ref={popupRef}>{children}</StyledPopup>;
};

DesktopPopup.propTypes = {
    children: PropTypes.node.isRequired,
};

export default DesktopPopup;
