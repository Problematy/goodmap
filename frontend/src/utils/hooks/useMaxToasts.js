import React, { useEffect } from "react";
import toast, {useToasterStore } from "react-hot-toast";

/**
 * Custom hook that limits the maximum number of visible toasts.
 * Automatically dismisses excess toasts when the limit is exceeded.
 *
 * @param {number} max - Maximum number of visible toasts (defaults to 1)
 * @returns {void}
 */
export function useMaxToasts(max = 1) {
    const { toasts } = useToasterStore();
  
    useEffect(() => {
        const excessToasts = toasts
            .filter((t) => t.visible)
            .filter((_, i) => i >= max);
        for (const t of excessToasts) {
            toast.dismiss(t.id);
        }
    }, [toasts, max]);
}