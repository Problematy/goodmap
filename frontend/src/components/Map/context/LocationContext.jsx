import React, {
    createContext,
    useContext,
    useState,
    useCallback,
    useEffect,
    useMemo,
    useRef,
} from 'react';
import PropTypes from 'prop-types';

const LocationContext = createContext();

// Geolocation configuration constants
const SPINNER_DELAY_MS = 300; // Delay before showing spinner to prevent flicker on fast responses
const GEOLOCATION_TIMEOUT_MS = 15000; // 15 seconds timeout for geolocation requests
const GEOLOCATION_MAX_AGE_MS = 300000; // 5 minutes cache for position data

// Error codes for consistent error handling
const GEOLOCATION_ERROR_CODES = {
    NOT_SUPPORTED: 0,
    PERMISSION_DENIED: 1,
    POSITION_UNAVAILABLE: 2,
    TIMEOUT: 3,
};

/**
 * Provider component that manages shared geolocation state across the map.
 * All location-dependent buttons share this state - when one gets permission,
 * all buttons become active.
 * Only auto-fetches location if permission was previously granted.
 * Otherwise, waits for explicit user action to request permission.
 */
export const LocationProvider = ({ children }) => {
    const [locationGranted, setLocationGranted] = useState(false);
    const [userPosition, setUserPosition] = useState(null);
    // 'unknown' | 'prompt' | 'granted' | 'denied'
    const [permissionState, setPermissionState] = useState('unknown');
    const [isRequestingLocation, setIsRequestingLocation] = useState(false);
    const [locationError, setLocationError] = useState(null);
    // Delayed loading indicator - only shows after 300ms to prevent flicker
    const [showLocationSpinner, setShowLocationSpinner] = useState(false);

    // Only show spinner after a delay to prevent flicker on fast responses
    useEffect(() => {
        let timer;
        if (isRequestingLocation) {
            timer = setTimeout(() => setShowLocationSpinner(true), SPINNER_DELAY_MS);
        } else {
            setShowLocationSpinner(false);
        }
        return () => clearTimeout(timer);
    }, [isRequestingLocation]);

    // Use ref to track request state without causing callback recreation
    const isRequestingRef = useRef(false);

    const requestGeolocation = useCallback((onSuccess, onError) => {
        if (!navigator.geolocation) {
            const errorObj = {
                code: GEOLOCATION_ERROR_CODES.NOT_SUPPORTED,
                message: 'Geolocation not supported',
            };
            setPermissionState('denied');
            setLocationGranted(false);
            setUserPosition(null);
            setLocationError(errorObj);
            onError?.(errorObj);
            return;
        }

        // Prevent multiple simultaneous requests
        if (isRequestingRef.current) {
            return;
        }

        isRequestingRef.current = true;
        setIsRequestingLocation(true);
        setLocationError(null);

        navigator.geolocation.getCurrentPosition(
            position => {
                const newPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                };
                setUserPosition(newPosition);
                setLocationGranted(true);
                setPermissionState('granted');
                isRequestingRef.current = false;
                setIsRequestingLocation(false);
                onSuccess?.(newPosition);
            },
            error => {
                const errorCode = error?.code ?? GEOLOCATION_ERROR_CODES.POSITION_UNAVAILABLE;
                const errorObj = {
                    code: errorCode,
                    message: error?.message ?? 'Unknown geolocation error',
                };

                // Only set permission state to 'denied' for actual permission denial
                // Other errors (TIMEOUT, POSITION_UNAVAILABLE) are transient and allow retries
                if (errorCode === GEOLOCATION_ERROR_CODES.PERMISSION_DENIED) {
                    setPermissionState('denied');
                    setLocationGranted(false);
                }

                setUserPosition(null);
                isRequestingRef.current = false;
                setIsRequestingLocation(false);
                setLocationError(errorObj);
                onError?.(errorObj);
            },
            {
                enableHighAccuracy: false,
                timeout: GEOLOCATION_TIMEOUT_MS,
                maximumAge: GEOLOCATION_MAX_AGE_MS,
            },
        );
    }, []);

    /**
     * Request geolocation with early return if position is already available.
     * If position is already available, calls onSuccess immediately.
     * If permission was explicitly denied, does nothing (tooltip provides feedback).
     * Otherwise requests geolocation.
     *
     * @param {Function} onSuccess - Callback when position is available, receives position object
     */
    const requestLocationWithFeedback = useCallback(
        onSuccess => {
            if (userPosition) {
                onSuccess?.(userPosition);
                return;
            }

            // Don't request if permission was explicitly denied - tooltip explains the issue
            // This avoids unnecessary state changes on mobile
            if (permissionState === 'denied') {
                return;
            }

            requestGeolocation(onSuccess);
        },
        [userPosition, requestGeolocation, permissionState],
    );

    // Check existing permission state without prompting the user.
    // Only auto-fetch location if permission was previously granted.
    useEffect(() => {
        let permissionStatus;
        let handleChange;

        const checkExistingPermission = async () => {
            if (!navigator.permissions || !navigator.geolocation) return;

            try {
                permissionStatus = await navigator.permissions.query({ name: 'geolocation' });
                setPermissionState(permissionStatus.state);

                if (permissionStatus.state === 'granted') {
                    requestGeolocation();
                }

                // Listen for permission changes
                handleChange = () => {
                    setPermissionState(permissionStatus.state);
                    if (permissionStatus.state === 'granted') {
                        requestGeolocation();
                    }
                };
                permissionStatus.addEventListener('change', handleChange);
            } catch {
                // Permissions API not supported - don't auto-request
            }
        };

        checkExistingPermission();

        return () => {
            if (permissionStatus && handleChange) {
                permissionStatus.removeEventListener('change', handleChange);
            }
        };
    }, [requestGeolocation]);

    const contextValue = useMemo(
        () => ({
            locationGranted,
            userPosition,
            setUserPosition,
            requestGeolocation,
            requestLocationWithFeedback,
            permissionState,
            isRequestingLocation,
            showLocationSpinner,
            locationError,
        }),
        [
            locationGranted,
            userPosition,
            setUserPosition,
            requestGeolocation,
            requestLocationWithFeedback,
            permissionState,
            isRequestingLocation,
            showLocationSpinner,
            locationError,
        ],
    );

    return <LocationContext.Provider value={contextValue}>{children}</LocationContext.Provider>;
};

LocationProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

/**
 * Hook to access the shared location context.
 * @returns {{locationGranted: boolean, userPosition: object|null, setUserPosition: function, requestGeolocation: function, requestLocationWithFeedback: function, permissionState: string, isRequestingLocation: boolean, showLocationSpinner: boolean, locationError: object|null}}
 */
export const useLocation = () => {
    const context = useContext(LocationContext);
    if (!context) {
        throw new Error('useLocation must be used within a LocationProvider');
    }
    return context;
};
