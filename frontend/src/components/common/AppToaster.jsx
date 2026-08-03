import React from 'react';
import { createPortal } from 'react-dom';
import toast, { ToastBar, Toaster } from 'react-hot-toast';
import { IconButton } from '@mui/material';
import Close from '@mui/icons-material/Close';
import { useMaxToasts } from '../../utils/hooks/useMaxToasts';

/**
 * Global toast notification component for displaying user feedback messages.
 * Uses react-hot-toast library with custom styling and close button.
 * Automatically limits the maximum number of toasts displayed using useMaxToasts hook.
 *
 * @returns {React.ReactElement} Toaster component configured for the application
 */
export const AppToaster = () => {
    useMaxToasts();

    // #main-row's stacking context would trap the toast below the MUI Dialog.
    // See the #overlay-root rule in platzky's styles.css.
    return createPortal(
        <Toaster
            position="top-center"
            reverseOrder={false}
            gutter={8}
            // Vertically centered: the success message fires right as the dialog
            // closes, and a small top-corner toast is easy to miss against a
            // full-screen map background.
            //
            // `position` must be 'absolute' so the offsets resolve against the
            // overlay layer - the library's default is 'fixed', which stays
            // viewport-relative regardless of the portal target and would center
            // the toast over the sidebar too.
            //
            // `bottom` must be overridden to 'auto': the library defaults to
            // `{ top: 16, bottom: 16, ... }`, and with both active the browser sizes
            // the container's height by spanning between them rather than shrinking
            // it to the toast's content height - which throws off translateY(-50%)'s
            // centering math.
            containerStyle={{
                position: 'absolute',
                top: '50%',
                bottom: 'auto',
                left: 0,
                right: 0,
                transform: 'translateY(-50%)',
            }}
            toastOptions={{
                duration: 8000,
                style: {
                    fontSize: '16px',
                    maxWidth: '500px',
                },
            }}
        >
            {t => (
                <ToastBar toast={t}>
                    {({ icon, message }) => (
                        <>
                            {icon}
                            {message}
                            {t.type !== 'loading' && (
                                <IconButton>
                                    <Close onClick={() => toast.dismiss(t.id)} />
                                </IconButton>
                            )}
                        </>
                    )}
                </ToastBar>
            )}
        </Toaster>,
        document.getElementById('overlay-root'),
    );
};
