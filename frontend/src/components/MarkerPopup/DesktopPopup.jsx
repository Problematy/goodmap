import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { Popup } from 'react-leaflet';
import { useLeafletContext } from '@react-leaflet/core';
import styled from 'styled-components';

/**
 * Styled Leaflet popup component with minimum width of 300px.
 */
const StyledPopup = styled(Popup)`
    min-width: 300px;
`;

/**
 * Desktop popup component for displaying location details.
 * Automatically opens the popup on mount via the parent Marker, which react-leaflet exposes as
 * the context's overlay container. This is a workaround since react-leaflet's Popup doesn't
 * support lazy loading or an .open() function.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Content to display inside the popup
 * @returns {React.ReactElement} Styled Popup component that auto-opens on mount
 */
const DesktopPopup = ({ children }) => {
    const context = useLeafletContext();

    useEffect(() => {
        // Popup binds itself to the overlay container in its own effect, and child effects run
        // before parent ones, so the popup is already bound by the time this runs.
        context.overlayContainer?.openPopup();
    }, [context]);

    return <StyledPopup>{children}</StyledPopup>;
};

DesktopPopup.propTypes = {
    children: PropTypes.node.isRequired,
};

export default DesktopPopup;
