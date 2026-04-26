"""Cards router — async CRUD + multi-tenant isolation."""
import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import RefreshToken

from apps.decks.models import Card, Deck

User = get_user_model()
URL = "/api/cards"
JSON = "application/json"


# --- async helpers ---------------------------------------------------------

@sync_to_async
def make_user(email: str, password: str = "pw-12345678"):
    return User.objects.create_user(email=email, password=password)


@sync_to_async
def make_deck(user, name: str = "Default"):
    return Deck.objects.create(user=user, name=name)


@sync_to_async
def make_card(deck, front: str = "Q", back: str = "A"):
    return Card.objects.create(deck=deck, front=front, back=back)


@sync_to_async
def make_token(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


@sync_to_async
def card_exists(card_id) -> bool:
    return Card.objects.filter(id=card_id).exists()


@sync_to_async
def reload_card_front(card_id) -> str:
    return Card.objects.get(id=card_id).front


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- 1) Auth: no token => 401 ---------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_card_without_token_returns_401(async_client):
    resp = await async_client.post(URL, data={}, content_type=JSON)
    assert resp.status_code == 401


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_cards_without_token_returns_401(async_client):
    resp = await async_client.get(f"{URL}?deck_id=00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 401


# --- 2) CRUD success ------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_card_in_own_deck_returns_201(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice, "Anatomy")
    token = await make_token(alice)

    resp = await async_client.post(
        URL,
        data={
            "deck_id": str(deck.id),
            "front": "What is the heart?",
            "back": "A muscular pump.",
        },
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["front"] == "What is the heart?"
    assert body["back"] == "A muscular pump."
    assert body["state"] == "new"
    assert body["deck_id"] == str(deck.id)
    assert body["id"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_cards_returns_only_decks_cards(async_client):
    alice = await make_user("alice@example.com")
    target_deck = await make_deck(alice, "Anatomy")
    other_deck = await make_deck(alice, "Histology")
    await make_card(target_deck, "Q1", "A1")
    await make_card(target_deck, "Q2", "A2")
    await make_card(other_deck, "Q3", "A3")
    token = await make_token(alice)

    resp = await async_client.get(
        f"{URL}?deck_id={target_deck.id}", headers=bearer(token)
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    fronts = {c["front"] for c in body["items"]}
    assert fronts == {"Q1", "Q2"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_card_returns_200_and_persists(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="Old front")
    token = await make_token(alice)

    resp = await async_client.patch(
        f"{URL}/{card.id}",
        data={"front": "New front"},
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    assert resp.json()["front"] == "New front"
    assert await reload_card_front(card.id) == "New front"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_my_card_returns_204(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck)
    token = await make_token(alice)

    resp = await async_client.delete(f"{URL}/{card.id}", headers=bearer(token))

    assert resp.status_code == 204
    assert not await card_exists(card.id)


# --- 3) Multi-tenant isolation: 404 across the deck->user join ------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_card_in_other_users_deck_returns_404(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob, "Bobs deck")
    alice_token = await make_token(alice)

    resp = await async_client.post(
        URL,
        data={
            "deck_id": str(bobs_deck.id),
            "front": "Hijack attempt",
            "back": "Should fail",
        },
        content_type=JSON,
        headers=bearer(alice_token),
    )

    # 404, not 403 — same enumeration-protection logic as decks.
    assert resp.status_code == 404


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_list_cards_of_other_users_deck_returns_empty(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob, "Bobs deck")
    await make_card(bobs_deck, "Bobs Q", "Bobs A")
    alice_token = await make_token(alice)

    resp = await async_client.get(
        f"{URL}?deck_id={bobs_deck.id}", headers=bearer(alice_token)
    )

    # Empty page (not 404) — query simply returns no rows. Mirrors how
    # GET /decks behaves for a foreign user (you only ever see your own).
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_other_users_card_returns_404(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob)
    bobs_card = await make_card(bobs_deck, front="secret")
    alice_token = await make_token(alice)

    resp = await async_client.patch(
        f"{URL}/{bobs_card.id}",
        data={"front": "hijacked"},
        content_type=JSON,
        headers=bearer(alice_token),
    )

    assert resp.status_code == 404
    # Row must stay intact.
    assert await reload_card_front(bobs_card.id) == "secret"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_other_users_card_returns_404(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob)
    bobs_card = await make_card(bobs_deck)
    alice_token = await make_token(alice)

    resp = await async_client.delete(
        f"{URL}/{bobs_card.id}", headers=bearer(alice_token)
    )

    assert resp.status_code == 404
    assert await card_exists(bobs_card.id)
