"""
Tests for image utility default detection.

This test suite validates that RecipezImageUtils correctly identifies
default_recipe.png filenames when processing image data.
"""
import pytest
from io import BytesIO
from recipez import create_app
from recipez.repository import UserRepository
from recipez.utils import RecipezSecretsUtils, RecipezImageUtils


@pytest.fixture()
def app():
    """Create and configure a test application instance."""
    return create_app({"TESTING": True})


@pytest.fixture()
def test_user(app):
    """Create a test user for image operations."""
    with app.app_context():
        email = "test@example.com"
        enc = RecipezSecretsUtils.encrypt(email)
        hmac = RecipezSecretsUtils.generate_hmac(email)
        user = UserRepository.create_user(enc, hmac, "testuser", "/static/img/default_user.png")
        token = RecipezSecretsUtils.generate_jwt(str(user.user_sub), [])
        return user, token


def test_image_utils_detects_default_recipe_png_filename(app, test_user):
    """
    RED TEST: Should detect 'default_recipe.png' filename from raw bytes.

    When image_data is raw bytes (not a file upload object), the code should
    assign filename = "default_recipe.png" (not "default.png").

    This test will FAIL initially because image.py:296 still uses "default.png".
    After implementation, it should pass.
    """
    user, token = test_user

    # Create raw bytes (simulating default image scenario)
    # In actual code, this comes from reading default_recipe.png file
    raw_image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # Minimal PNG header

    with app.app_context():
        with app.test_request_context():
            # Mock the validator to bypass actual validation
            import recipez.utils.image as image_module
            original_validator = image_module.RecipezImageValidator

            class MockValidator:
                def __init__(self, filename, image_data):
                    self.filename = filename
                    self.image_data = image_data

                def _validate_image(self):
                    # Check that filename is default_recipe.png (not default.png)
                    assert self.filename == "default_recipe.png", \
                        f"Expected filename 'default_recipe.png', got '{self.filename}'"
                    return []

                def _scrub_image(self, file_data, new_format):
                    return file_data

            # Temporarily replace validator to intercept filename
            image_module.RecipezImageValidator = MockValidator

            try:
                # This will fail if image.py:296 still uses "default.png"
                result = RecipezImageUtils.create_image(
                    authorization=f"Bearer {token}",
                    request=app.test_request_context().request,
                    author_id=user.user_id,
                    image_data=raw_image_bytes,  # Raw bytes, no .filename attribute
                    old_image_url=None
                )
            finally:
                # Restore original validator
                image_module.RecipezImageValidator = original_validator


def test_image_utils_preserves_uploaded_filename(app, test_user):
    """
    Verify that file upload objects preserve their original filename.

    When image_data has a .filename attribute (file upload), that filename
    should be used, not the default.
    """
    user, token = test_user

    # Create mock file upload object
    class MockFileUpload:
        def __init__(self, filename, content):
            self.filename = filename
            self._content = content

        def read(self):
            return self._content

    uploaded_file = MockFileUpload("user_uploaded.png", b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

    with app.app_context():
        with app.test_request_context():
            import recipez.utils.image as image_module
            original_validator = image_module.RecipezImageValidator

            class MockValidator:
                def __init__(self, filename, image_data):
                    self.filename = filename
                    self.image_data = image_data

                def _validate_image(self):
                    # Verify uploaded filename preserved
                    assert self.filename == "user_uploaded.png", \
                        f"Expected filename 'user_uploaded.png', got '{self.filename}'"
                    return []

                def _scrub_image(self, file_data, new_format):
                    return file_data

            image_module.RecipezImageValidator = MockValidator

            try:
                result = RecipezImageUtils.create_image(
                    authorization=f"Bearer {token}",
                    request=app.test_request_context().request,
                    author_id=user.user_id,
                    image_data=uploaded_file,  # Has .filename attribute
                    old_image_url=None
                )
            finally:
                image_module.RecipezImageValidator = original_validator


def test_deletion_logic_preserves_default_recipe_png(app, test_user, monkeypatch):
    """
    RED TEST (P1 CRITICAL): Deletion logic must NOT delete default_recipe.png.

    When replacing an image with old_image_url = "/static/img/default_recipe.png",
    the deletion logic should skip deletion (preserve the default file).

    This test will FAIL initially because image.py:305 only checks for "default.png".
    After implementation with OR logic, it should pass.
    """
    user, token = test_user

    # Track whether os.remove was called
    remove_called_with = []
    original_remove = __import__('os').remove

    def mock_remove(path):
        remove_called_with.append(path)
        # Don't actually remove anything in tests

    monkeypatch.setattr("os.remove", mock_remove)

    # Mock path.exists to return True
    monkeypatch.setattr("os.path.exists", lambda p: True)

    raw_image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    with app.app_context():
        with app.test_request_context():
            import recipez.utils.image as image_module
            original_validator = image_module.RecipezImageValidator

            class MockValidator:
                def __init__(self, filename, image_data):
                    pass

                def _validate_image(self):
                    return []

                def _scrub_image(self, file_data, new_format):
                    return file_data

            image_module.RecipezImageValidator = MockValidator

            # Mock the file write operations
            monkeypatch.setattr("builtins.open", lambda *args, **kwargs: __import__('io').BytesIO())

            try:
                result = RecipezImageUtils.create_image(
                    authorization=f"Bearer {token}",
                    request=app.test_request_context().request,
                    author_id=user.user_id,
                    image_data=raw_image_bytes,
                    old_image_url="/static/img/default_recipe.png"  # Should NOT be deleted
                )

                # Assert that os.remove was NOT called (default preserved)
                assert len(remove_called_with) == 0, \
                    f"default_recipe.png should NOT be deleted, but os.remove was called with: {remove_called_with}"

            finally:
                image_module.RecipezImageValidator = original_validator


def test_deletion_logic_preserves_default_user_png(app, test_user, monkeypatch):
    """
    RED TEST (P1 CRITICAL): Deletion logic must NOT delete default_user.png.

    When replacing an image with old_image_url = "/static/img/default_user.png",
    the deletion logic should skip deletion (preserve the default file).

    This test validates the dual-default preservation logic.
    """
    user, token = test_user

    remove_called_with = []

    def mock_remove(path):
        remove_called_with.append(path)

    monkeypatch.setattr("os.remove", mock_remove)
    monkeypatch.setattr("os.path.exists", lambda p: True)

    raw_image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    with app.app_context():
        with app.test_request_context():
            import recipez.utils.image as image_module
            original_validator = image_module.RecipezImageValidator

            class MockValidator:
                def __init__(self, filename, image_data):
                    pass

                def _validate_image(self):
                    return []

                def _scrub_image(self, file_data, new_format):
                    return file_data

            image_module.RecipezImageValidator = MockValidator

            monkeypatch.setattr("builtins.open", lambda *args, **kwargs: __import__('io').BytesIO())

            try:
                result = RecipezImageUtils.create_image(
                    authorization=f"Bearer {token}",
                    request=app.test_request_context().request,
                    author_id=user.user_id,
                    image_data=raw_image_bytes,
                    old_image_url="/static/img/default_user.png"  # Should NOT be deleted
                )

                assert len(remove_called_with) == 0, \
                    f"default_user.png should NOT be deleted, but os.remove was called with: {remove_called_with}"

            finally:
                image_module.RecipezImageValidator = original_validator


def test_deletion_logic_deletes_custom_images(app, test_user, monkeypatch):
    """
    Verify deletion logic DOES delete custom (non-default) images.

    This ensures the refactored logic still properly deletes user-uploaded images.
    """
    user, token = test_user

    remove_called_with = []

    def mock_remove(path):
        remove_called_with.append(path)

    monkeypatch.setattr("os.remove", mock_remove)
    monkeypatch.setattr("os.path.exists", lambda p: True)

    raw_image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    with app.app_context():
        with app.test_request_context():
            import recipez.utils.image as image_module
            original_validator = image_module.RecipezImageValidator

            class MockValidator:
                def __init__(self, filename, image_data):
                    pass

                def _validate_image(self):
                    return []

                def _scrub_image(self, file_data, new_format):
                    return file_data

            image_module.RecipezImageValidator = MockValidator

            monkeypatch.setattr("builtins.open", lambda *args, **kwargs: __import__('io').BytesIO())

            try:
                result = RecipezImageUtils.create_image(
                    authorization=f"Bearer {token}",
                    request=app.test_request_context().request,
                    author_id=user.user_id,
                    image_data=raw_image_bytes,
                    old_image_url="/static/uploads/custom-uuid-123.png"  # SHOULD be deleted
                )

                # Assert that os.remove WAS called for custom image
                assert len(remove_called_with) == 1, \
                    f"Custom image should be deleted, but os.remove was called {len(remove_called_with)} times: {remove_called_with}"

            finally:
                image_module.RecipezImageValidator = original_validator
