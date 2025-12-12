"""
Tests for ImageRepository default image protection.

This test suite validates that ImageRepository.delete_image() never deletes
default images (default_recipe.png, default_user.png) from the filesystem.
"""
import pytest
import uuid
from recipez import create_app
from recipez.repository import ImageRepository, UserRepository
from recipez.utils import RecipezSecretsUtils


@pytest.fixture()
def app():
    """Create and configure a test application instance."""
    return create_app({"TESTING": True})


def _create_unique_user(app, prefix="repo"):
    """Create a test user with unique identifiers."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"{prefix}_{unique_id}@example.com"
    enc = RecipezSecretsUtils.encrypt(email)
    hmac = RecipezSecretsUtils.generate_hmac(email)
    user = UserRepository.create_user(enc, hmac, f"{prefix}_{unique_id}", "/static/img/default_user.png")
    return user


def test_delete_image_preserves_default_recipe_png(app, monkeypatch):
    """
    Verify that delete_image() does NOT delete default_recipe.png from filesystem.
    """
    remove_called = []

    def mock_remove(path):
        remove_called.append(path)

    monkeypatch.setattr("os.remove", mock_remove)
    monkeypatch.setattr("os.path.exists", lambda p: True)

    with app.app_context():
        user = _create_unique_user(app, "repo1")

        # Create an image record pointing to default_recipe.png
        image = ImageRepository.create_image(
            "/static/img/default_recipe.png",
            str(user.user_id)
        )

        # Delete the image
        result = ImageRepository.delete_image(str(image.image_id))

        # Verify deletion succeeded (DB record removed)
        assert result is True

        # Verify os.remove was NOT called (file preserved)
        assert len(remove_called) == 0, \
            f"default_recipe.png should NOT be deleted, but os.remove was called: {remove_called}"


def test_delete_image_preserves_default_user_png(app, monkeypatch):
    """
    Verify that delete_image() does NOT delete default_user.png from filesystem.
    """
    remove_called = []

    def mock_remove(path):
        remove_called.append(path)

    monkeypatch.setattr("os.remove", mock_remove)
    monkeypatch.setattr("os.path.exists", lambda p: True)

    with app.app_context():
        user = _create_unique_user(app, "repo2")

        # Create an image record pointing to default_user.png
        image = ImageRepository.create_image(
            "/static/img/default_user.png",
            str(user.user_id)
        )

        # Delete the image
        result = ImageRepository.delete_image(str(image.image_id))

        # Verify deletion succeeded (DB record removed)
        assert result is True

        # Verify os.remove was NOT called (file preserved)
        assert len(remove_called) == 0, \
            f"default_user.png should NOT be deleted, but os.remove was called: {remove_called}"


def test_delete_image_deletes_custom_images(app, monkeypatch):
    """
    Verify that delete_image() DOES delete custom uploaded images.
    """
    remove_called = []

    def mock_remove(path):
        remove_called.append(path)

    monkeypatch.setattr("os.remove", mock_remove)
    monkeypatch.setattr("os.path.exists", lambda p: True)

    with app.app_context():
        user = _create_unique_user(app, "repo3")

        # Create an image record pointing to a custom image
        image = ImageRepository.create_image(
            "/static/uploads/abc123-custom-image.png",
            str(user.user_id)
        )

        # Delete the image
        result = ImageRepository.delete_image(str(image.image_id))

        # Verify deletion succeeded (DB record removed)
        assert result is True

        # Verify os.remove WAS called for custom image
        assert len(remove_called) == 1, \
            f"Custom image should be deleted, but os.remove called {len(remove_called)} times"
        assert "abc123-custom-image.png" in remove_called[0], \
            f"Expected custom image path, got: {remove_called}"


def test_delete_image_handles_nonexistent_file_gracefully(app, monkeypatch):
    """
    Verify that delete_image() succeeds even if the file doesn't exist on disk.
    """
    monkeypatch.setattr("os.path.exists", lambda p: False)

    with app.app_context():
        user = _create_unique_user(app, "repo4")

        # Create an image record
        image = ImageRepository.create_image(
            "/static/uploads/missing-image.png",
            str(user.user_id)
        )

        # Delete should succeed even if file is missing
        result = ImageRepository.delete_image(str(image.image_id))

        assert result is True


def test_delete_image_returns_false_for_nonexistent_id(app):
    """
    Verify that delete_image() returns False for non-existent image IDs.
    """
    with app.app_context():
        # Try to delete a non-existent image
        result = ImageRepository.delete_image("00000000-0000-0000-0000-000000000000")

        assert result is False
