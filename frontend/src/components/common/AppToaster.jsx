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

    // Portalled to document.body (like MUI's Dialog) rather than rendered in place:
    // this component lives deep inside the map's component tree, where an ancestor
    // (e.g. a Leaflet pane) can establish its own stacking context and trap the
    // toast's z-index there, so it loses to the Dialog's portal-level stacking no
    // matter how high the z-index is set.
    return createPortal(
        <Toaster
            position="top-center"
            reverseOrder={false}
            gutter={8}
            // Centered on the viewport rather than pinned to the top: the success
            // message fires right as the dialog closes, and a small top-corner toast
            // is easy to miss against a full-screen map background.
            //
            // `bottom` must be overridden to 'auto' too: react-hot-toast's container
            // defaults to `{ top: 16, bottom: 16, ... }`, and with both `top` and
            // `bottom` active the browser sizes the container's height by spanning
            // between them (leaving it anchored to the lower half of the viewport)
            // rather than shrinking it to the toast's actual content height - which
            // throws off translateY(-50%)'s centering math.
            containerStyle={{
                zIndex: 99999999,
                top: '50%',
                bottom: 'auto',
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
        document.body,
    );
};
