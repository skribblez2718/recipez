import types
import pytest

from recipez import create_app
from recipez.utils import authn as authn_utils, authz as authz_utils
from recipez.utils.email import RecipezEmailUtils


@pytest.fixture()
def app(monkeypatch):
    """Create app with patched auth decorators and email utils."""

    def fake_jwt_required(fn):
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper

    # Patch decorators to bypass auth
    monkeypatch.setattr(authn_utils.RecipezAuthNUtils, "jwt_required", staticmethod(fake_jwt_required))
    monkeypatch.setattr(
        authz_utils.RecipezAuthZUtils, "scope_required", staticmethod(lambda scope: (lambda f: f))
    )

    # Patch email utils to avoid sending real emails
    monkeypatch.setattr(
        RecipezEmailUtils,
        "email_invite",
        staticmethod(lambda request, payload: {"response": {"message": "ok"}}),
    )
    monkeypatch.setattr(
        RecipezEmailUtils,
        "email_recipe_share",
        staticmethod(lambda request, payload: {"response": {"message": "ok"}}),
    )

    app = create_app({"TESTING": True})
    return app


def test_email_invite_invalid_email(app):
    client = app.test_client()
    resp = client.post(
        "/api/email/invite",
        json={"email": "bad", "invite_link": "https://x.com", "sender_name": "Alice"},
    )
    assert resp.status_code == 400
    assert resp.json["response"]["error"] == "Failed to send invitation email"


def test_email_recipe_share_invalid_url(app):
    client = app.test_client()
    resp = client.post(
        "/api/email/recipe-share",
        json={
            "email": "user@example.com",
            "recipe_name": "Pasta",
            "recipe_link": "not-a-url",
            "sender_name": "Bob",
        },
    )
    assert resp.status_code == 400
    assert resp.json["response"]["error"] == "Failed to send recipe sharing email"
