import { useEffect, useState } from 'react';

/**
 * Custom hook that debounces a value.
 * Returns a debounced version of the value that only updates after the specified delay.
 * Useful for delaying expensive operations like API calls until user input stabilizes.
 *
 * @param {*} value - Value to debounce
 * @param {number} delay - Delay in milliseconds (defaults to 500ms if not provided)
 * @returns {*} Debounced value
 */
function useDebounce(value, delay = 500) {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);

        return () => {
            clearTimeout(timer);
        };
    }, [value, delay]);

    return debouncedValue;
}

export default useDebounce;
