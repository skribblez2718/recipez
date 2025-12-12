import pytest

from recipez import create_app


@pytest.fixture()
def app():
    return create_app({"TESTING": True})


def test_create_user_invalid_email(app):
    client = app.test_client()
    resp = client.post("/api/user/create", json={"email": "bad"})
    assert resp.status_code == 400
    assert resp.json["response"]["error"] == "Failed to create user"
