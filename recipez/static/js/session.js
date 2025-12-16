/**
 * Session Manager - Handles 401/403 response interception
 *
 * This module provides automatic redirect to login when API calls
 * return 401 (Unauthorized) or 403 (Forbidden) responses.
 *
 * The module overrides window.fetch to work transparently with existing code.
 */
(function() {
    'use strict';

    const LOGIN_URL = '/auth/login/email';

    /**
     * Redirect to login page with return URL
     */
    function redirectToLogin() {
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `${LOGIN_URL}?next=${returnUrl}`;
    }

    /**
     * Override window.fetch to intercept 401/403 responses
     * Only redirects for API calls (URLs containing '/api/')
     */
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const response = await originalFetch.apply(this, args);

        // Check for authentication failure on API calls
        if (response.status === 401 || response.status === 403) {
            // Extract URL from first argument (can be string or Request object)
            const url = args[0]?.url || args[0];

            // Only redirect for API calls, not for external resources or static assets
            if (typeof url === 'string' && url.includes('/api/')) {
                console.info('Session: API returned ' + response.status + ', redirecting to login');
                redirectToLogin();
            }
        }

        return response;
    };
})();
