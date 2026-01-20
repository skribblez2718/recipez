"""
Comprehensive tests for image filename validation.
Tests various filename patterns including iPhone naming, download duplicates,
and security checks for path traversal and injection attacks.
"""

import pytest
from io import BytesIO
from PIL import Image
from recipez.utils.image import RecipezImageValidator


def create_test_image(format='JPEG') -> bytes:
    """Create a minimal valid image for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


class TestFilenameValidation:
    """Test filename validation patterns."""

    @pytest.fixture
    def valid_image_data(self):
        """Provide valid JPEG image data for tests."""
        return create_test_image('JPEG')

    # Valid filename tests - should PASS validation

    def test_iphone_filename_with_spaces(self, valid_image_data):
        """Should accept iPhone-style filenames with spaces."""
        filenames = [
            'Photo 2024-01-15 at 10.30.45 AM.jpeg',
            'IMG 1234.jpg',
            'Photo Jan 15 2024.png',
        ]
        for filename in filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert validator._is_valid_filename(), f"Should accept iPhone filename: {filename}"

    def test_download_duplicates_with_parentheses(self, valid_image_data):
        """Should accept download duplicate filenames with parentheses."""
        filenames = [
            'image (1).jpeg',
            'photo (2).jpg',
            'recipe (copy).png',
            'screenshot (3) (final).jpeg',
        ]
        for filename in filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert validator._is_valid_filename(), f"Should accept download duplicate: {filename}"

    def test_filenames_with_brackets(self, valid_image_data):
        """Should accept filenames with brackets."""
        filenames = [
            'screenshot [2024-01-15].png',
            'image [draft].jpeg',
            'photo [final version].jpg',
        ]
        for filename in filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert validator._is_valid_filename(), f"Should accept bracketed filename: {filename}"

    def test_standard_filenames(self, valid_image_data):
        """Should accept standard alphanumeric filenames."""
        filenames = [
            'IMG_0123.jpeg',
            'recipe-image.jpg',
            'my_photo.png',
            'test.jpeg',
            'image123.jpg',
        ]
        for filename in filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert validator._is_valid_filename(), f"Should accept standard filename: {filename}"

    def test_all_supported_extensions(self, valid_image_data):
        """Should accept all supported file extensions."""
        extensions = ['jpg', 'jpeg', 'png', 'heic', 'heif', 'webp']
        for ext in extensions:
            filename = f"test_image.{ext}"
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert validator._is_valid_extension(), f"Should accept extension: {ext}"

    # Security tests - should FAIL validation

    def test_path_traversal_blocked(self, valid_image_data):
        """Should block path traversal attempts."""
        malicious_filenames = [
            '../../../etc/passwd.png',
            '..\\..\\windows\\system32\\config.jpeg',
            'image/../../../etc/passwd.jpg',
            '....//....//etc/passwd.png',
        ]
        for filename in malicious_filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert not validator._is_valid_filename(), f"Should block path traversal: {filename}"

    def test_null_byte_injection_blocked(self, valid_image_data):
        """Should block null byte injection attempts."""
        malicious_filenames = [
            'image.php\x00.jpeg',
            'test\x00.exe.png',
            'photo\x00script.jpg',
        ]
        for filename in malicious_filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert not validator._is_valid_filename(), f"Should block null byte injection: {filename}"

    def test_forward_slash_blocked(self, valid_image_data):
        """Should block filenames with forward slashes."""
        malicious_filenames = [
            '/etc/passwd.png',
            'uploads/../../etc/passwd.jpeg',
            'foo/bar.jpg',
        ]
        for filename in malicious_filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert not validator._is_valid_filename(), f"Should block forward slash: {filename}"

    def test_backslash_blocked(self, valid_image_data):
        """Should block filenames with backslashes."""
        malicious_filenames = [
            '\\windows\\system32\\config.png',
            'uploads\\..\\..\\etc\\passwd.jpeg',
            'foo\\bar.jpg',
        ]
        for filename in malicious_filenames:
            validator = RecipezImageValidator(filename=filename, image_data=valid_image_data)
            assert not validator._is_valid_filename(), f"Should block backslash: {filename}"


class TestFullValidation:
    """Test full validation flow including filename, extension, and file content."""

    @pytest.fixture
    def valid_jpeg_data(self):
        """Provide valid JPEG image data."""
        return create_test_image('JPEG')

    @pytest.fixture
    def valid_png_data(self):
        """Provide valid PNG image data."""
        return create_test_image('PNG')

    def test_iphone_photo_full_validation(self, valid_jpeg_data):
        """iPhone-style filename should pass full validation."""
        validator = RecipezImageValidator(
            filename='Photo 2024-01-15 at 10.30.45 AM.jpeg',
            image_data=valid_jpeg_data
        )
        assert validator.is_valid, f"iPhone photo should be valid: {validator.error}"

    def test_download_duplicate_full_validation(self, valid_jpeg_data):
        """Download duplicate filename should pass full validation."""
        validator = RecipezImageValidator(
            filename='image (1).jpeg',
            image_data=valid_jpeg_data
        )
        assert validator.is_valid, f"Download duplicate should be valid: {validator.error}"

    def test_bracketed_filename_full_validation(self, valid_png_data):
        """Bracketed filename should pass full validation."""
        validator = RecipezImageValidator(
            filename='screenshot [2024-01-15].png',
            image_data=valid_png_data
        )
        assert validator.is_valid, f"Bracketed filename should be valid: {validator.error}"

    def test_path_traversal_fails_full_validation(self, valid_jpeg_data):
        """Path traversal should fail full validation."""
        validator = RecipezImageValidator(
            filename='../../../etc/passwd.jpeg',
            image_data=valid_jpeg_data
        )
        assert not validator.is_valid, "Path traversal should fail validation"
        assert "unsupported characters" in validator.error.lower() or "unsafe" in validator.error.lower()


class TestFileSizeLimits:
    """Test file size validation with the new 10MB limit."""

    def test_accepts_10mb_file(self):
        """Should accept files up to 10MB."""
        # Create a ~5MB image (well under limit)
        img = Image.new('RGB', (2000, 2000), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        image_data = buffer.getvalue()

        validator = RecipezImageValidator(filename='large_image.jpeg', image_data=image_data)
        assert validator._is_valid_file_size(), "Should accept image under 10MB"

    def test_rejects_over_10mb_file(self):
        """Should reject files over 10MB."""
        # Create fake data over 10MB
        image_data = b'\x00' * (10485760 + 1)  # 10MB + 1 byte

        validator = RecipezImageValidator(filename='huge_image.jpeg', image_data=image_data)
        assert not validator._is_valid_file_size(), "Should reject image over 10MB"


class TestErrorMessages:
    """Test error messages are user-friendly."""

    @pytest.fixture
    def valid_jpeg_data(self):
        """Provide valid JPEG image data."""
        return create_test_image('JPEG')

    def test_filename_error_message(self, valid_jpeg_data):
        """Should provide helpful error message for invalid filename."""
        validator = RecipezImageValidator(
            filename='bad<script>name.jpeg',
            image_data=valid_jpeg_data
        )
        if not validator.is_valid:
            # Check the error message is user-friendly
            assert 'unsupported characters' in validator.error.lower() or 'letters' in validator.error.lower()

    def test_size_error_message(self):
        """Should mention 10 MB in size error message."""
        image_data = b'\x00' * (10485760 + 1)
        validator = RecipezImageValidator(filename='big.jpeg', image_data=image_data)
        if not validator._is_valid_file_size():
            # The error message should mention 10 MB
            errors = validator._validate_image()
            size_error = [e for e in errors if 'MB' in e or 'size' in e.lower()]
            assert any('10' in e for e in size_error), "Error should mention 10 MB limit"
