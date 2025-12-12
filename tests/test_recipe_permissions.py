import types
import uuid

import pytest
from flask import g

from recipez import create_app
from recipez.repository import RecipeRepository
from recipez.utils import authn as authn_utils
from recipez.utils import authz as authz_utils


@pytest.fixture()
def app(monkeypatch):
    """Create app with patched auth decorators for testing."""

    def fake_jwt_required(fn):
        def wrapper(*args, **kwargs):
            g.user = types.SimpleNamespace(user_id="user1")
            g.jwt_scopes = ["recipe:update", "recipe:delete"]
            return fn(*args, **kwargs)

        return wrapper

    # Patch decorators before app creation so blueprints use them
    monkeypatch.setattr(authn_utils.RecipezAuthNUtils, "jwt_required", staticmethod(fake_jwt_required))
    monkeypatch.setattr(
        authz_utils.RecipezAuthZUtils, "recipe_update_required", staticmethod(lambda f: f)
    )
    monkeypatch.setattr(
        authz_utils.RecipezAuthZUtils, "recipe_delete_required", staticmethod(lambda f: f)
    )

    app = create_app({"TESTING": True})
    return app


def _recipe(author_id: str):
    return types.SimpleNamespace(
        recipe_id=str(uuid.uuid4()),
        recipe_name="name",
        recipe_description="desc",
        recipe_category_id=str(uuid.uuid4()),
        recipe_image_id=str(uuid.uuid4()),
        recipe_author_id=author_id,
    )


def test_update_recipe_forbidden(app, monkeypatch):
    """Ensure users cannot update recipes they do not own."""
    rid = str(uuid.uuid4())

    monkeypatch.setattr(
        RecipeRepository,
        "get_recipe_by_id",
        staticmethod(lambda _id: _recipe("other")),
    )
    # fail if update is attempted
    monkeypatch.setattr(
        RecipeRepository,
        "update_recipe",
        staticmethod(lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError())),
    )

    client = app.test_client()
    resp = client.put(f"/api/recipe/update/{rid}", json={"recipe_name": "new"})
    assert resp.status_code == 400
    assert (
        resp.json["response"]["error"]
        == "You do not have permission to update this recipe"
    )


def test_update_recipe_success(app, monkeypatch):
    rid = str(uuid.uuid4())

    monkeypatch.setattr(
        RecipeRepository, "get_recipe_by_id", staticmethod(lambda _id: _recipe("user1"))
    )
    monkeypatch.setattr(
        RecipeRepository, "update_recipe", staticmethod(lambda *a, **k: True)
    )

    client = app.test_client()
    resp = client.put(f"/api/recipe/update/{rid}", json={"recipe_name": "new"})
    assert resp.json["response"]["success"] is True


def test_delete_recipe_forbidden(app, monkeypatch):
    rid = str(uuid.uuid4())

    monkeypatch.setattr(
        RecipeRepository,
        "get_recipe_by_id",
        staticmethod(lambda _id: _recipe("other")),
    )
    monkeypatch.setattr(
        RecipeRepository,
        "delete_recipe",
        staticmethod(lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError())),
    )

    client = app.test_client()
    resp = client.delete(f"/api/recipe/delete/{rid}")
    assert resp.status_code == 400
    assert (
        resp.json["response"]["error"]
        == "You do not have permission to delete this recipe"
    )


def test_delete_recipe_success(app, monkeypatch):
    rid = str(uuid.uuid4())

    monkeypatch.setattr(
        RecipeRepository, "get_recipe_by_id", staticmethod(lambda _id: _recipe("user1"))
    )
    monkeypatch.setattr(
        RecipeRepository, "delete_recipe", staticmethod(lambda *a, **k: True)
    )

    client = app.test_client()
    resp = client.delete(f"/api/recipe/delete/{rid}")
    assert resp.json["response"]["success"] is True

