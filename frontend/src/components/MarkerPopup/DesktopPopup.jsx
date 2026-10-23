import React, { useCallback, useEffect, useRef } from 'react';
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
    const popupRef = useRef(null);

    useEffect(() => {
        // Popup binds itself to the overlay container in its own effect, and child effects run
        // before parent ones, so the popup is already bound by the time this runs.
        context.overlayContainer?.openPopup();
    }, [context]);

    // react-leaflet re-lays out and re-pans the popup only when its children change. An image
    // the server rendered grows the popup when it arrives, after that - upwards, as the popup
    // hangs from its marker - so without this its top, close button included, ends up above
    // the map. `load` and `error` do not bubble, hence the capture phase. A callback ref,
    // because react-leaflet renders the children only once Leaflet has made the popup's
    // content node, after this component's own effects have run.
    const contentRef = useCallback(node => {
        const relayout = () => popupRef.current?.update();
        if (node) {
            node.addEventListener('load', relayout, true);
            node.addEventListener('error', relayout, true);
        }
    }, []);

    return (
        <StyledPopup ref={popupRef}>
            <div ref={contentRef}>{children}</div>
        </StyledPopup>
    );
};

DesktopPopup.propTypes = {
    children: PropTypes.node.isRequired,
};

export default DesktopPopup;
