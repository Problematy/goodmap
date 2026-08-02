/**
 * Test constants for reusable test data and messages
 */

/**
 * Error and success messages expected in the UI
 */
export const ERROR_MESSAGES = {
    LOCATION_SERVICES: 'Please enable location services to suggest a new point.',
    // Matches FILE_SIZES.MAX_MB via PHOTO_SCHEMA below (Math.floor(max_size_bytes / 1024 / 1024)).
    FILE_TOO_LARGE: 'The selected file is too large. Please select a file smaller than 5MiB.',
    PHOTO_PROCESSING_FAILED: "Couldn't process this photo. Please try a different file.",
    LOCATION_NOT_AVAILABLE: /Location not available.*enable location services/i,
    REQUIRED_FIELDS: /Please fill in required fields/i,
    SUBMISSION_ERROR: /Error suggesting location/i,
    SUBMISSION_SUCCESS: /Location suggested successfully/i,
};

/**
 * Test coordinates for geolocation mocking
 */
export const TEST_COORDINATES = {
    DEFAULT: { lat: 0, lng: 0 },
    NULL: { lat: null, lng: null },
};

/**
 * File size constants for testing file uploads
 */
export const FILE_SIZES = {
    MAX_MB: 5,
    OVER_LIMIT_MB: 6,
    VALID_TEST_MB: 4,
};

/**
 * Photo constraints mirroring the backend's AttachmentConfig default (see goodmap.py)
 */
export const PHOTO_SCHEMA = {
    allowed_extensions: ['jpeg', 'jpg'],
    allowed_mime_types: ['image/jpeg'],
    max_size_bytes: FILE_SIZES.MAX_MB * 1024 * 1024,
};

/**
 * Simple location schema with minimal fields for testing
 */
export const SIMPLE_SCHEMA = {
    obligatory_fields: [['name', 'str']],
    categories: {},
    photo: PHOTO_SCHEMA,
};

/**
 * Full location schema with all field types for comprehensive testing
 */
export const FULL_SCHEMA = {
    obligatory_fields: [
        ['name', 'str'],
        ['accessible_by', 'list'],
        ['type_of_place', 'str'],
    ],
    categories: {
        accessible_by: ['bikes', 'cars', 'pedestrians'],
        type_of_place: ['big bridge', 'small bridge'],
    },
    photo: PHOTO_SCHEMA,
};
