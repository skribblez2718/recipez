"""
Security tests for URL validation to prevent XSS and path traversal.
Tests Issue 1 (CRITICAL): Stored XSS via Arbitrary User Profile Image URL Injection
"""

import pytest
from recipez.utils.validation import validate_image_url


class TestImageUrlValidation:
    """Test validate_image_url security function"""

    def test_reject_javascript_scheme(self):
        """Should reject javascript: URLs to prevent XSS"""
        malicious_urls = [
            'javascript:alert("XSS")',
            'javascript:alert(document.cookie)',
            'JAVASCRIPT:void(0)',
        ]
        for url in malicious_urls:
            assert validate_image_url(url) is False, f"Failed to reject: {url}"

    def test_reject_data_scheme(self):
        """Should reject data: URLs to prevent XSS"""
        malicious_urls = [
            'data:text/html,<script>alert("XSS")</script>',
            'data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=',
            'DATA:image/png;base64,malicious',
        ]
        for url in malicious_urls:
            assert validate_image_url(url) is False, f"Failed to reject: {url}"

    def test_reject_vbscript_scheme(self):
        """Should reject vbscript: URLs to prevent XSS"""
        malicious_urls = [
            'vbscript:msgbox("XSS")',
            'VBSCRIPT:alert',
        ]
        for url in malicious_urls:
            assert validate_image_url(url) is False, f"Failed to reject: {url}"

    def test_reject_file_scheme(self):
        """Should reject file: URLs"""
        assert validate_image_url('file:///etc/passwd') is False

    def test_reject_onerror_injection(self):
        """Should reject URLs with onerror handlers"""
        malicious_urls = [
            '/static/img/test.png" onerror="alert(\'XSS\')',
            'https://example.com/img.png onerror=alert(1)',
        ]
        for url in malicious_urls:
            assert validate_image_url(url) is False, f"Failed to reject: {url}"

    def test_reject_path_traversal(self):
        """Should reject path traversal attempts"""
        malicious_urls = [
            '/static/../../../etc/passwd',
            '/static/uploads/../../etc/shadow',
            '/static/img/../uploads/../../../etc/passwd',
        ]
        for url in malicious_urls:
            assert validate_image_url(url) is False, f"Failed to reject: {url}"

    def test_reject_excessive_path_depth(self):
        """Should reject paths with too many segments"""
        url = '/static/uploads/deep/path/too/many/segments.png'
        assert validate_image_url(url) is False

    def test_reject_invalid_extensions(self):
        """Should reject non-image file extensions"""
        malicious_urls = [
            '/static/img/script.js',
            '/static/uploads/malware.exe',
            '/static/img/payload.php',
        ]
        for url in malicious_urls:
            assert validate_image_url(url) is False, f"Failed to reject: {url}"

    def test_reject_http_scheme(self):
        """Should reject insecure http:// URLs (HTTPS only for external)"""
        url = 'http://example.com/image.png'
        assert validate_image_url(url) is False

    def test_accept_valid_static_img_paths(self):
        """Should accept valid /static/img/ paths"""
        valid_urls = [
            '/static/img/default_recipe.png',
            '/static/img/default_user.png',
            '/static/img/logo.jpg',
        ]
        for url in valid_urls:
            assert validate_image_url(url) is True, f"Failed to accept: {url}"

    def test_accept_valid_static_uploads_paths(self):
        """Should accept valid /static/uploads/ UUID paths"""
        valid_urls = [
            '/static/uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890.png',
            '/static/uploads/12345678-1234-5678-1234-567890abcdef.jpg',
            '/static/uploads/test-image-123.png',
        ]
        for url in valid_urls:
            assert validate_image_url(url) is True, f"Failed to accept: {url}"

    def test_reject_none_value(self):
        """Should reject None values"""
        assert validate_image_url(None) is False

    def test_reject_empty_string(self):
        """Should reject empty strings"""
        assert validate_image_url('') is False

    def test_reject_non_string_types(self):
        """Should reject non-string types"""
        assert validate_image_url(123) is False
        assert validate_image_url(['url']) is False
        assert validate_image_url({'url': 'test'}) is False
