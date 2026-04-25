"""End-to-end auth flow: register -> login -> refresh."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"

JSON = "application/json"


@pytest.mark.django_db
def test_register_returns_201_and_token_pair(client):
    resp = client.post(
        REGISTER_URL,
        data={"email": "alice@example.com", "password": "supersecret123"},
        content_type=JSON,
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["access"]
    assert body["refresh"]
    assert get_user_model().objects.filter(email="alice@example.com").exists()


@pytest.mark.django_db
def test_register_with_duplicate_email_returns_400(client):
    """Case-insensitive: pre-existing 'alice@…' must reject 'Alice@…'."""
    get_user_model().objects.create_user(
        email="alice@example.com",
        password="pre-existing-pw",
    )

    resp = client.post(
        REGISTER_URL,
        data={"email": "Alice@Example.COM", "password": "supersecret123"},
        content_type=JSON,
    )

    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.django_db
def test_login_with_valid_credentials_returns_token_pair(client):
    get_user_model().objects.create_user(
        email="bob@example.com",
        password="correct-horse-battery",
    )

    resp = client.post(
        LOGIN_URL,
        data={"email": "bob@example.com", "password": "correct-horse-battery"},
        content_type=JSON,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["access"]
    assert body["refresh"]


@pytest.mark.django_db
def test_login_with_wrong_password_returns_401(client):
    get_user_model().objects.create_user(
        email="carol@example.com",
        password="real-password",
    )

    resp = client.post(
        LOGIN_URL,
        data={"email": "carol@example.com", "password": "wrong-password"},
        content_type=JSON,
    )

    assert resp.status_code == 401


@pytest.mark.django_db
def test_refresh_with_valid_token_returns_new_access(client):
    get_user_model().objects.create_user(
        email="dave@example.com",
        password="pw-12345678",
    )
    login = client.post(
        LOGIN_URL,
        data={"email": "dave@example.com", "password": "pw-12345678"},
        content_type=JSON,
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh"]

    resp = client.post(
        REFRESH_URL,
        data={"refresh": refresh_token},
        content_type=JSON,
    )

    assert resp.status_code == 200
    assert resp.json()["access"]
