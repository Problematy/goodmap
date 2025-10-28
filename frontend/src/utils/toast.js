import { toast as toastify } from 'react-hot-toast';

/**
 * Toast notification utility object.
 * Provides simplified access to react-hot-toast notification methods.
 *
 * @property {Function} success - Displays a success toast notification
 * @property {Function} error - Displays an error toast notification
 * @property {Function} info - Displays an info/loading toast notification
 */
export const toast = {
    success: toastify.success,
    error: toastify.error,
    info: toastify.loading,
};
