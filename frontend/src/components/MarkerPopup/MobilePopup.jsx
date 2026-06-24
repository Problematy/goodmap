import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogTitle, IconButton, Slide } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useLeafletContext } from '@react-leaflet/core';

/**
 * Mobile-optimized popup component for displaying location details.
 * Renders as a bottom sheet dialog that slides up from the bottom of the screen.
 * Automatically pans the map to center the marker when opened.
 * Compatible with react-leaflet's Marker component through overlay container integration.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Content to display inside the popup dialog
 * @returns {React.ReactElement} Material-UI Dialog styled as a bottom sheet
 */
export const MobilePopup = ({ children }) => {
    const [isOpen, setIsOpen] = useState(true);
    const context = useLeafletContext();

    // useEffect below contains workaround to bo compatible with Popoup from react-leaflet
    // where it's Marker (parent of Popup) is responsible for closing the Popup
    useEffect(() => {
        const overlayContainer = context?.overlayContainer;

        const centerMap = latlng => {
            const offset = 0.003;
            const newLat = latlng.lat - offset;
            context.map.panTo([newLat, latlng.lng], { duration: 0.5 });
        };

        if (overlayContainer) {
            centerMap(overlayContainer._latlng);

            overlayContainer.on('click', place => {
                centerMap(place.latlng);
                setIsOpen(true);
            });
        }

        return () => {
            if (overlayContainer) {
                overlayContainer.off('click');
            }
        };
    }, [context]);

    const handleClose = () => {
        setIsOpen(false);
    };

    return (
        <Dialog
            open={isOpen}
            onClose={handleClose}
            fullWidth
            maxWidth="md"
            TransitionComponent={SlideTransition}
            PaperProps={{
                style: {
                    position: 'fixed',
                    bottom: 0,
                    margin: 0,
                    width: '100%',
                    maxHeight: '90%',
                    borderRadius: '16px 16px 0 0',
                    padding: '1px 1px',
                },
            }}
        >
            <DialogTitle style={{ textAlign: 'center', padding: '2px 16px' }}>
                <IconButton
                    aria-label="close"
                    onClick={handleClose}
                    style={{ position: 'absolute', right: 8, top: 8 }}
                >
                    <CloseIcon />
                </IconButton>
            </DialogTitle>
            <DialogContent sx={{ padding: '8px' }}>{children}</DialogContent>
        </Dialog>
    );
};

/**
 * Slide transition component for the mobile popup dialog.
 * Animates the dialog sliding up from the bottom of the screen.
 *
 * @param {Object} props - Transition props passed by Material-UI
 * @param {React.Ref} ref - Forwarded ref for the transition component
 * @returns {React.ReactElement} Slide transition component
 */
const SlideTransition = React.forwardRef(function Transition(props, ref) {
    return <Slide direction="up" ref={ref} {...props} />;
});
