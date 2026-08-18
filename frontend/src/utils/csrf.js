/**
 * Utility functions for CSRF token handling.
 *
 * CSRF (Cross-Site Request Forgery) protection prevents malicious websites
 * from making unauthorized requests to our API on behalf of users.
 *
 * The CSRF token is provided by the backend in a meta tag and must be
 * included in the X-CSRFToken header for all POST/PUT/DELETE requests.
 */

/**
 * Gets the CSRF token from the page's meta tag.
 *
 * The backend sets a meta tag like:
 * <meta name="csrf-token" content="TOKEN_VALUE">
 *
 * This token must be included in the X-CSRFToken header for all
 * state-changing requests (POST, PUT, PATCH, DELETE).
 *
 * @returns {string} The CSRF token
 * @throws {Error} If the CSRF token meta tag is missing or empty
 *
 * @example
 * const csrfToken = getCsrfToken();
 * axios.post('/api/suggest-new-point', data, {
 *   headers: { 'X-CSRFToken': csrfToken }
 * });
 */
export const getCsrfToken = () => {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    const token = metaTag?.getAttribute('content');

    if (!token) {
        throw new Error(
            'CSRF token not found. Ensure the backend includes <meta name="csrf-token" content="..."> in the page HTML.',
        );
    }

    return token;
};
