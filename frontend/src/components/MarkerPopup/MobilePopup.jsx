import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogTitle, IconButton, Slide } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useLeafletContext } from '@react-leaflet/core';

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
                    maxHeight: '50%',
                    borderRadius: '16px 16px 0 0',
                },
            }}
        >
            <DialogTitle style={{ textAlign: 'center', padding: '8px 16px' }}>
                <IconButton
                    aria-label="close"
                    onClick={handleClose}
                    style={{ position: 'absolute', right: 8, top: 8 }}
                >
                    <CloseIcon />
                </IconButton>
            </DialogTitle>
            <DialogContent>{children}</DialogContent>
        </Dialog>
    );
};

const SlideTransition = React.forwardRef(function Transition(props, ref) {
    return <Slide direction="up" ref={ref} {...props} />;
});
