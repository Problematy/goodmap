import React from 'react';
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

    return (
        <Toaster
            position="top-center"
            reverseOrder={false}
            gutter={8}
            containerStyle={{ zIndex: 99999999, top: 120 }}
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
        </Toaster>
    );
};
