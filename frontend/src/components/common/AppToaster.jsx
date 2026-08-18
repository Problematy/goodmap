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
const AppToaster = () => {
    useMaxToasts();

    // #main-row's stacking context would trap the toast below the MUI Dialog.
    // See the #overlay-root rule in platzky's styles.css.
    return createPortal(
        <Toaster
            position="top-center"
            reverseOrder={false}
            gutter={8}
            // Placed mid-map: a toast in the top corner is easy to miss against a
            // full-screen map. `bottom` must be 'auto' - the library defaults it to
            // 16, which stretches the container and drops the toast far below here.
            containerStyle={{
                top: '50%',
                bottom: 'auto',
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

export default AppToaster;
