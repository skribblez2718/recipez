"""
Tests for recipe default image handling.

This test suite validates that recipe creation uses default_recipe.png
when no image is uploaded by the user.
"""
import pytest
from pathlib import Path
from recipez import create_app
from recipez.repository import UserRepository, CategoryRepository, RecipeRepository
from recipez.utils import RecipezSecretsUtils, RecipezRecipeUtils


@pytest.fixture()
def app():
    """Create and configure a test application instance."""
    return create_app({"TESTING": True})


@pytest.fixture()
def test_user(app):
    """Create a test user for recipe operations."""
    with app.app_context():
        email = "test@example.com"
        enc = RecipezSecretsUtils.encrypt(email)
        hmac = RecipezSecretsUtils.generate_hmac(email)
        user = UserRepository.create_user(enc, hmac, "testuser", "/static/img/default_user.png")
        token = RecipezSecretsUtils.generate_jwt(str(user.user_sub), [])
        return user, token


def test_recipe_default_image_path_uses_default_recipe_png(app, test_user, monkeypatch):
    """
    RED TEST: Should use default_recipe.png path when creating recipe without image.

    This test will FAIL initially because recipe.py:326 still references default.png.
    After implementation, it should pass.
    """
    user, token = test_user

    # Track which file path was opened
    opened_paths = []
    original_open = open

    def mock_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        # Still call original open to allow actual file operations
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    with app.app_context():
        # Create category for recipe
        category = CategoryRepository.create_category("Test Category", user.user_id)

        # Create recipe without providing image_data (should use default)
        result = RecipezRecipeUtils.create_recipe_image(
            authorization=f"Bearer {token}",
            request=app.test_request_context().request,
            author_id=user.user_id,
            image_data=None  # No image provided - should use default
        )

        # Assert that default_recipe.png was opened (not default.png)
        assert any("default_recipe.png" in path for path in opened_paths), \
            f"Expected default_recipe.png to be opened, but found: {opened_paths}"

        # Assert that old default.png was NOT opened
        assert not any("default.png" in path and "default_recipe.png" not in path for path in opened_paths), \
            f"Old default.png should not be used, but found in: {opened_paths}"


def test_recipe_default_image_file_exists():
    """
    Prerequisite test: Verify default_recipe.png file exists.

    This test ensures the physical file was renamed before code changes.
    """
    from pathlib import Path

    # Calculate expected path to default_recipe.png
    recipe_utils_path = Path(__file__).parent.parent / "recipez" / "utils" / "recipe.py"
    static_img_dir = recipe_utils_path.parent.parent / "static" / "img"
    default_recipe_path = static_img_dir / "default_recipe.png"
    default_user_path = static_img_dir / "default_user.png"
    old_default_path = static_img_dir / "default.png"

    # Assert new files exist
    assert default_recipe_path.exists(), \
        f"default_recipe.png must exist at {default_recipe_path}"
    assert default_user_path.exists(), \
        f"default_user.png must exist at {default_user_path}"

    # Warn if old file still exists (might be symlink for transition)
    if old_default_path.exists():
        print(f"WARNING: default.png still exists at {old_default_path} - may be symlink for transition")
