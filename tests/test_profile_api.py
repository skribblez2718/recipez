import pytest
from recipez import create_app
from recipez.repository import UserRepository, CategoryRepository, ImageRepository, RecipeRepository, IngredientRepository
from recipez.utils import RecipezSecretsUtils


@pytest.fixture()
def app():
    return create_app({"TESTING": True})


def _create_user(app):
    with app.app_context():
        email = "user@example.com"
        enc = RecipezSecretsUtils.encrypt(email)
        hmac = RecipezSecretsUtils.generate_hmac(email)
        user = UserRepository.create_user(enc, hmac, "user", "/static/img/default_user.png")
        token = RecipezSecretsUtils.generate_jwt(str(user.user_sub), [])
        return user, token


def test_generate_api_key(app):
    user, token = _create_user(app)
    client = app.test_client()
    resp = client.post("/api/profile/api-key", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "api_key" in resp.json["response"]


def test_update_profile_image(app):
    user, token = _create_user(app)
    client = app.test_client()
    resp = client.put(
        "/api/profile/image",
        headers={"Authorization": f"Bearer {token}"},
        json={"image_url": "/static/img/test.png"},
    )
    assert resp.status_code == 200
    assert resp.json["response"]["message"] == "Profile image updated"
    with app.app_context():
        updated = UserRepository.get_user_by_id(user.user_id)
        assert updated.user_profile_image_url == "/static/img/test.png"


def test_grocery_list(app, monkeypatch):
    user, token = _create_user(app)
    with app.app_context():
        cat = CategoryRepository.create_category("TestCat", user.user_id)
        img = ImageRepository.create_image("/static/img/default_recipe.png", user.user_id)
        recipe = RecipeRepository.create_recipe(
            "R1", "desc", "desc", cat.category_id, img.image_id, user.user_id
        )
        IngredientRepository.create_ingredient("Tomato", "2", "pcs", str(recipe.recipe_id), user.user_id)
    monkeypatch.setattr("recipez.utils.email.RecipezEmailUtils.send_email", lambda *args, **kwargs: {"response": {"success": True}})
    client = app.test_client()
    resp = client.post(
        "/api/profile/grocery-list",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipe_ids": [str(recipe.recipe_id)]},
    )
    assert resp.status_code == 200
    assert "Produce" in resp.json["response"]
