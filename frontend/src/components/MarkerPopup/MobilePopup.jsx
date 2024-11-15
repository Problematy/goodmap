import { Dialog, DialogContent, DialogTitle, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import React from 'react';

export const MobilePopup = ({ isOpen, onCloseHandler, children }) => (
    <Dialog
        open={isOpen}
        onClose={onCloseHandler}
        fullWidth
        maxWidth="md"
        style={{
            position: 'fixed',
            bottom: 0,
            margin: 0,
        }}
        PaperProps={{
            style: {
                position: 'fixed',
                bottom: 0,
                margin: 0,
                width: '100%',
                maxHeight: '50%',
            },
        }}
    >
        <DialogTitle>
            <IconButton
                aria-label="close"
                onClick={onCloseHandler}
                style={{ position: 'absolute', right: 8, top: 8 }}
            >
                <CloseIcon />
            </IconButton>
        </DialogTitle>

        <DialogContent>{children}</DialogContent>
    </Dialog>
);
