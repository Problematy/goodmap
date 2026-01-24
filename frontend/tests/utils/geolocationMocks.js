/**
 * Geolocation mocking utilities for testing components that use navigator.geolocation
 */

/**
 * Mocks geolocation with successful position retrieval
 * @param {number} lat - Latitude (default: 0)
 * @param {number} lng - Longitude (default: 0)
 */
export const mockGeolocationSuccess = (lat = 0, lng = 0) => {
    globalThis.navigator.geolocation = {
        getCurrentPosition: jest.fn(success =>
            success({ coords: { latitude: lat, longitude: lng } }),
        ),
    };
};

/**
 * Mocks geolocation with error callback
 * @param {number} code - Error code (1=PERMISSION_DENIED, 2=POSITION_UNAVAILABLE, 3=TIMEOUT)
 * @param {string} message - Error message
 */
export const mockGeolocationError = (code = 1, message = 'User denied geolocation') => {
    globalThis.navigator.geolocation = {
        getCurrentPosition: jest.fn((success, error) => error({ code, message })),
    };
};

/**
 * Mocks geolocation as unsupported (undefined)
 */
export const mockGeolocationUnsupported = () => {
    globalThis.navigator.geolocation = undefined;
};

/**
 * Mocks geolocation with null position (for testing position validation)
 */
export const mockGeolocationWithNullPosition = () => {
    globalThis.navigator.geolocation = {
        getCurrentPosition: jest.fn(callback => {
            callback({ coords: { latitude: null, lng: null } });
        }),
    };
};
