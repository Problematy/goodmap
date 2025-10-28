import React, { useEffect, useRef } from 'react';
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
export const DesktopPopup = ({ children }) => {
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
