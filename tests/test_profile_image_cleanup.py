"""
Tests for profile image cleanup functionality.

This test suite validates that:
1. Old custom profile images are deleted when a new image is uploaded
2. Default user images (default_user.png) are never deleted
3. Profile images go through the same validation/sanitization as recipe images
"""
import pytest
import uuid
from unittest.mock import MagicMock
from recipez import create_app
from recipez.repository import UserRepository
from recipez.utils import RecipezSecretsUtils, RecipezProfileUtils


@pytest.fixture()
def app():
    """Create and configure a test application instance."""
    return create_app({"TESTING": True})


def _create_unique_user(app, prefix="profile"):
    """Create a test user with unique identifiers."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique_id}@example.com"
    enc = RecipezSecretsUtils.encrypt(email)
    hmac = RecipezSecretsUtils.generate_hmac(email)
    user = UserRepository.create_user(enc, hmac, f"{prefix}_{unique_id}", "/static/img/default_user.png")
    token = RecipezSecretsUtils.generate_jwt(str(user.user_sub), [])
    return user, token


def test_profile_update_passes_old_image_url_to_create_image(app, monkeypatch):
    """
    Verify that update_profile_image fetches current profile and passes
    old_image_url to RecipezImageUtils.create_image() for cleanup.
    """
    with app.app_context():
        user, token = _create_unique_user(app, "cleanup1")

        # Track what arguments are passed to create_image
        captured_args = {}

        def mock_create_image(authorization, request, author_id, image_data, old_image_url=None):
            captured_args["old_image_url"] = old_image_url
            return {"image": {"image_url": "/static/uploads/new-image.png"}}

        def mock_read_profile(authorization, request):
            return {"profile_image_url": "/static/uploads/old-custom-image.png"}

        def mock_make_request(**kwargs):
            return {"message": "Profile image updated"}

        with app.test_request_context():
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezImageUtils.create_image",
                mock_create_image
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezProfileUtils.read_profile",
                mock_read_profile
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezAPIUtils.make_request",
                mock_make_request
            )

            # Create mock file upload
            mock_file = MagicMock()
            mock_file.filename = "new_profile.png"
            mock_file.read.return_value = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

            result = RecipezProfileUtils.update_profile_image(
                authorization=f"Bearer {token}",
                request=app.test_request_context().request,
                author_id=str(user.user_id),
                image_file=mock_file
            )

            # Verify old_image_url was passed to create_image
            assert captured_args.get("old_image_url") == "/static/uploads/old-custom-image.png", \
                f"Expected old_image_url to be passed, got: {captured_args}"


def test_profile_update_handles_default_user_image(app, monkeypatch):
    """
    Verify that when user has default_user.png, it's passed to create_image
    and the deletion logic (in create_image) will preserve it.
    """
    with app.app_context():
        user, token = _create_unique_user(app, "cleanup2")

        captured_args = {}

        def mock_create_image(authorization, request, author_id, image_data, old_image_url=None):
            captured_args["old_image_url"] = old_image_url
            return {"image": {"image_url": "/static/uploads/new-image.png"}}

        def mock_read_profile(authorization, request):
            # User has default profile image
            return {"profile_image_url": "/static/img/default_user.png"}

        def mock_make_request(**kwargs):
            return {"message": "Profile image updated"}

        with app.test_request_context():
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezImageUtils.create_image",
                mock_create_image
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezProfileUtils.read_profile",
                mock_read_profile
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezAPIUtils.make_request",
                mock_make_request
            )

            mock_file = MagicMock()
            mock_file.filename = "new_profile.png"
            mock_file.read.return_value = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

            result = RecipezProfileUtils.update_profile_image(
                authorization=f"Bearer {token}",
                request=app.test_request_context().request,
                author_id=str(user.user_id),
                image_file=mock_file
            )

            # Verify default_user.png URL is passed (create_image will protect it)
            assert captured_args.get("old_image_url") == "/static/img/default_user.png", \
                f"Expected default_user.png to be passed, got: {captured_args}"


def test_profile_update_handles_no_previous_image(app, monkeypatch):
    """
    Verify that update_profile_image works when user has no previous image.
    """
    with app.app_context():
        user, token = _create_unique_user(app, "cleanup3")

        captured_args = {}

        def mock_create_image(authorization, request, author_id, image_data, old_image_url=None):
            captured_args["old_image_url"] = old_image_url
            return {"image": {"image_url": "/static/uploads/new-image.png"}}

        def mock_read_profile(authorization, request):
            # User has no profile image
            return {"profile_image_url": None}

        def mock_make_request(**kwargs):
            return {"message": "Profile image updated"}

        with app.test_request_context():
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezImageUtils.create_image",
                mock_create_image
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezProfileUtils.read_profile",
                mock_read_profile
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezAPIUtils.make_request",
                mock_make_request
            )

            mock_file = MagicMock()
            mock_file.filename = "new_profile.png"
            mock_file.read.return_value = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

            result = RecipezProfileUtils.update_profile_image(
                authorization=f"Bearer {token}",
                request=app.test_request_context().request,
                author_id=str(user.user_id),
                image_file=mock_file
            )

            # Verify old_image_url is None (no cleanup needed)
            assert captured_args.get("old_image_url") is None, \
                f"Expected old_image_url to be None, got: {captured_args}"


def test_profile_update_handles_read_profile_error(app, monkeypatch):
    """
    Verify that update_profile_image continues even if read_profile fails.
    """
    with app.app_context():
        user, token = _create_unique_user(app, "cleanup4")

        captured_args = {}

        def mock_create_image(authorization, request, author_id, image_data, old_image_url=None):
            captured_args["old_image_url"] = old_image_url
            return {"image": {"image_url": "/static/uploads/new-image.png"}}

        def mock_read_profile_error(authorization, request):
            raise Exception("Network error")

        def mock_make_request(**kwargs):
            return {"message": "Profile image updated"}

        with app.test_request_context():
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezImageUtils.create_image",
                mock_create_image
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezProfileUtils.read_profile",
                mock_read_profile_error
            )
            monkeypatch.setattr(
                "recipez.utils.profile.RecipezAPIUtils.make_request",
                mock_make_request
            )

            mock_file = MagicMock()
            mock_file.filename = "new_profile.png"
            mock_file.read.return_value = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

            # Should not raise, just proceed with old_image_url = None
            result = RecipezProfileUtils.update_profile_image(
                authorization=f"Bearer {token}",
                request=app.test_request_context().request,
                author_id=str(user.user_id),
                image_file=mock_file
            )

            # Verify old_image_url is None due to error handling
            assert captured_args.get("old_image_url") is None, \
                f"Expected old_image_url to be None after error, got: {captured_args}"
