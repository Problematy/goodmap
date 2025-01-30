import React, { useEffect, useRef } from 'react';
import { Popup } from 'react-leaflet';
import styled from 'styled-components';

const StyledPopup = styled(Popup)`
    min-width: 300px;
`;

// DesktopPopup is a workaround for not existing lazy loading Popup as
// react-leaflet Popup doesn't support .open() function
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
