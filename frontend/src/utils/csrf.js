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
 * Gets the CSRF token from the page's meta tag, with fallback to legacy API endpoint.
 *
 * Preferred method: The backend sets a meta tag like:
 * <meta name="csrf-token" content="TOKEN_VALUE">
 *
 * Fallback (DEPRECATED): Fetches token from /api/generate-csrf-token endpoint.
 * This fallback exists for backward compatibility but will be removed in a future version.
 *
 * This token must be included in the X-CSRFToken header for all
 * state-changing requests (POST, PUT, PATCH, DELETE).
 *
 * @returns {Promise<string>} The CSRF token
 * @throws {Error} If CSRF token cannot be obtained from either source
 *
 * @example
 * const csrfToken = await getCsrfToken();
 * axios.post('/api/suggest-new-point', data, {
 *   headers: { 'X-CSRFToken': csrfToken }
 * });
 */
export const getCsrfToken = async () => {
    const metaTag = document.querySelector('meta[name="csrf-token"]');

    // Try to get token from meta tag first (preferred method)
    if (metaTag) {
        const token = metaTag.getAttribute('content');
        if (token) {
            return token;
        }
    }

    // Fallback to legacy API endpoint (DEPRECATED)
    console.warn(
        '⚠️ DEPRECATION WARNING: CSRF token meta tag not found. ' +
            'Falling back to /api/generate-csrf-token endpoint. ' +
            'This fallback is DEPRECATED and will be removed in a future version. ' +
            'Please ensure the backend includes <meta name="csrf-token" content="..."> in the page HTML.',
    );

    try {
        const response = await fetch('/api/generate-csrf-token');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        if (!data.csrf_token) {
            throw new Error('API response missing csrf_token field');
        }
        return data.csrf_token;
    } catch (error) {
        console.error('Failed to fetch CSRF token from legacy endpoint:', error);
        throw new Error(
            'CSRF token not found. Neither meta tag nor /api/generate-csrf-token endpoint provided a valid token.',
        );
    }
};

/**
 * Creates axios headers object with CSRF token.
 *
 * Convenience function to generate headers with CSRF token
 * for use with axios requests.
 *
 * @param {Object} additionalHeaders - Optional additional headers to merge
 * @returns {Promise<Object>} Promise resolving to headers object with X-CSRFToken
 *
 * @example
 * const headers = await getCsrfHeaders({ 'Content-Type': 'application/json' });
 * axios.post('/api/suggest-new-point', data, { headers });
 */
export const getCsrfHeaders = async (additionalHeaders = {}) => {
    const token = await getCsrfToken();
    return {
        'X-CSRFToken': token,
        ...additionalHeaders,
    };
};
