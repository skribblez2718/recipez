"""
Security tests for HTTP security headers.
Tests Issue 5 (HIGH): Missing Session Security Headers
"""

import pytest


class TestSecurityHeaders:
    """Test security headers are present in responses"""

    def test_x_frame_options_present(self, client):
        """Should set X-Frame-Options: DENY to prevent clickjacking"""
        response = client.get('/')
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_x_content_type_options_present(self, client):
        """Should set X-Content-Type-Options: nosniff to prevent MIME-sniffing"""
        response = client.get('/')
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

    def test_x_xss_protection_present(self, client):
        """Should set X-XSS-Protection for legacy browser protection"""
        response = client.get('/')
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'

    def test_referrer_policy_present(self, client):
        """Should set Referrer-Policy to limit information leakage"""
        response = client.get('/')
        assert 'Referrer-Policy' in response.headers
        assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'

    def test_hsts_present_in_production(self, app, client):
        """Should set HSTS header when SESSION_COOKIE_SECURE is True (production)"""
        # Simulate production config
        app.config['SESSION_COOKIE_SECURE'] = True
        response = client.get('/')

        # HSTS only set in production (when HTTPS enforced)
        if app.config.get('SESSION_COOKIE_SECURE'):
            assert 'Strict-Transport-Security' in response.headers
            assert 'max-age=31536000' in response.headers['Strict-Transport-Security']
            assert 'includeSubDomains' in response.headers['Strict-Transport-Security']

    def test_csp_img_src_directive(self, client):
        """Should include img-src directive in CSP header (Issue 6)"""
        response = client.get('/')
        csp = response.headers.get('Content-Security-Policy', '')

        # Issue 6 (MEDIUM): img-src should restrict image sources
        assert "img-src 'self' data:" in csp

    def test_csp_frame_ancestors_directive(self, client):
        """Should include frame-ancestors directive in CSP header (Issue 5)"""
        response = client.get('/')
        csp = response.headers.get('Content-Security-Policy', '')

        # Issue 5 (HIGH): frame-ancestors prevents clickjacking via CSP
        assert "frame-ancestors 'none'" in csp
