"""Decks router — async CRUD + multi-tenant isolation."""
import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import RefreshToken

from apps.decks.models import Deck

User = get_user_model()
URL = "/api/decks"
JSON = "application/json"


# --- async helpers (test setup hits DB synchronously then crosses over) ---

@sync_to_async
def make_user(email: str, password: str = "pw-12345678"):
    return User.objects.create_user(email=email, password=password)


@sync_to_async
def make_deck(user, name: str = "Default"):
    return Deck.objects.create(user=user, name=name)


@sync_to_async
def make_token(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


@sync_to_async
def deck_exists(deck_id) -> bool:
    return Deck.objects.filter(id=deck_id, deleted_at__isnull=True).exists()


@sync_to_async
def reload_name(deck_id) -> str:
    return Deck.objects.get(id=deck_id).name


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- 1) Auth: no token => 401 ----------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_without_token_returns_401(async_client):
    resp = await async_client.post(
        URL,
        data={"name": "X"},
        content_type=JSON,
    )
    assert resp.status_code == 401


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_without_token_returns_401(async_client):
    resp = await async_client.get(URL)
    assert resp.status_code == 401


# --- 2) CRUD success -------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_returns_201_and_persists(async_client):
    user = await make_user("alice@example.com")
    token = await make_token(user)

    resp = await async_client.post(
        URL,
        data={"name": "Anatomy"},
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Anatomy"
    assert body["id"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_returns_only_owner_decks(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    await make_deck(alice, "Anatomy")
    await make_deck(alice, "Histology")
    await make_deck(bob, "Bobs deck")
    token = await make_token(alice)

    resp = await async_client.get(URL, headers=bearer(token))

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    names = {d["name"] for d in body["items"]}
    assert names == {"Anatomy", "Histology"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_my_deck_returns_200(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice, "Old name")
    token = await make_token(alice)

    resp = await async_client.patch(
        f"{URL}/{deck.id}",
        data={"name": "New name"},
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    assert resp.json()["name"] == "New name"
    assert await reload_name(deck.id) == "New name"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_my_deck_returns_204(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice, "To delete")
    token = await make_token(alice)

    resp = await async_client.delete(
        f"{URL}/{deck.id}",
        headers=bearer(token),
    )

    assert resp.status_code == 204
    assert not await deck_exists(deck.id)


# --- 3) Multi-tenant isolation: 404 when touching someone else's deck ------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_other_users_deck_returns_404(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs = await make_deck(bob, "Bobs secret")
    alice_token = await make_token(alice)

    resp = await async_client.patch(
        f"{URL}/{bobs.id}",
        data={"name": "Hijacked"},
        content_type=JSON,
        headers=bearer(alice_token),
    )

    # 404, NOT 403 — leaking 'this id exists but isnt yours' would let an
    # attacker enumerate Bobs deck ids.
    assert resp.status_code == 404
    # And the row stays intact.
    assert await reload_name(bobs.id) == "Bobs secret"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_other_users_deck_returns_404(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs = await make_deck(bob, "Bobs deck")
    alice_token = await make_token(alice)

    resp = await async_client.delete(
        f"{URL}/{bobs.id}",
        headers=bearer(alice_token),
    )

    assert resp.status_code == 404
    assert await deck_exists(bobs.id)
