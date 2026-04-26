"""Sync pull (GET /sync/changes) — composite cursor + tombstones."""
from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja_jwt.tokens import RefreshToken

from apps.decks.models import Card, Deck
from apps.sync.api import _encode_cursor

User = get_user_model()
SYNC_URL = "/api/sync/changes"
DECKS_URL = "/api/decks"
CARDS_URL = "/api/cards"
JSON = "application/json"


# --- async helpers ---------------------------------------------------------

@sync_to_async
def make_user(email: str, password: str = "pw-12345678"):
    return User.objects.create_user(email=email, password=password)


@sync_to_async
def make_deck(user, **kwargs):
    defaults = {"name": "Default"}
    defaults.update(kwargs)
    return Deck.objects.create(user=user, **defaults)


@sync_to_async
def make_card(deck, **kwargs):
    defaults = {"front": "Q", "back": "A"}
    defaults.update(kwargs)
    return Card.objects.create(deck=deck, **defaults)


@sync_to_async
def make_token(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


@sync_to_async
def force_card_updated_at(card_id, ts):
    """Bypass auto_now to wedge a known timestamp in for cursor tests."""
    Card.objects.filter(id=card_id).update(updated_at=ts)


@sync_to_async
def force_deck_updated_at(deck_id, ts):
    Deck.objects.filter(id=deck_id).update(updated_at=ts)


@sync_to_async
def get_card_raw(card_id):
    return Card.objects.get(id=card_id)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- 1) Auth ---------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_changes_without_token_returns_401(async_client):
    resp = await async_client.get(SYNC_URL)
    assert resp.status_code == 401


# --- 2) Tombstones surface here even though CRUD hides them ---------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_soft_deleted_card_is_hidden_in_crud_but_visible_in_sync(
    async_client,
):
    """The whole point of soft delete: CRUD goes silent, sync exposes
    the tombstone so other devices can apply the deletion locally."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="to-delete")
    token = await make_token(alice)

    # Soft delete via the normal CRUD endpoint.
    delete_resp = await async_client.delete(
        f"{CARDS_URL}/{card.id}", headers=bearer(token)
    )
    assert delete_resp.status_code == 204

    # GET /cards no longer surfaces it.
    list_resp = await async_client.get(
        f"{CARDS_URL}?deck_id={deck.id}", headers=bearer(token)
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] == 0

    # But /sync/changes does — and ``deleted_at`` is populated so the
    # client knows it's a tombstone, not a regular update.
    sync_resp = await async_client.get(SYNC_URL, headers=bearer(token))
    assert sync_resp.status_code == 200
    body = sync_resp.json()
    matched = [c for c in body["cards"] if c["id"] == str(card.id)]
    assert len(matched) == 1
    assert matched[0]["deleted_at"] is not None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_soft_deleted_deck_appears_in_sync_with_tombstone(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice, name="to-delete")
    card = await make_card(deck, front="child")
    token = await make_token(alice)

    delete_resp = await async_client.delete(
        f"{DECKS_URL}/{deck.id}", headers=bearer(token)
    )
    assert delete_resp.status_code == 204

    # CRUD list goes silent.
    list_resp = await async_client.get(DECKS_URL, headers=bearer(token))
    assert list_resp.json()["count"] == 0
    cards_resp = await async_client.get(
        f"{CARDS_URL}?deck_id={deck.id}", headers=bearer(token)
    )
    assert cards_resp.json()["count"] == 0

    # Sync emits the deck tombstone and cascaded child-card tombstone.
    sync_resp = await async_client.get(SYNC_URL, headers=bearer(token))
    body = sync_resp.json()
    matched = [d for d in body["decks"] if d["id"] == str(deck.id)]
    assert len(matched) == 1
    assert matched[0]["deleted_at"] is not None
    matched_cards = [c for c in body["cards"] if c["id"] == str(card.id)]
    assert len(matched_cards) == 1
    assert matched_cards[0]["deleted_at"] is not None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_soft_delete_after_cursor_is_returned_as_tombstone(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="later-delete")
    token = await make_token(alice)

    first = await async_client.get(SYNC_URL, headers=bearer(token))
    cursor = first.json()["next_cursor"]

    delete_resp = await async_client.delete(
        f"{CARDS_URL}/{card.id}", headers=bearer(token)
    )
    assert delete_resp.status_code == 204

    second = await async_client.get(
        SYNC_URL, data={"cursor": cursor}, headers=bearer(token)
    )
    matched = [c for c in second.json()["cards"] if c["id"] == str(card.id)]
    assert len(matched) == 1
    assert matched[0]["deleted_at"] is not None


# --- 3) Composite cursor breaks ties correctly ----------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_composite_cursor_advances_through_a_tied_updated_at_group(
    async_client,
):
    """Three cards with the EXACT same ``updated_at`` are the worst-case
    for a timestamp-only cursor. The composite ``(updated_at, id)``
    cursor must walk them in id order, returning the strict tail when
    the cursor lands inside the group — no skip, no duplicate.
    """
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    # Push the deck firmly into the past so its updated_at can never
    # tie with the cards' fixed_ts.
    past = timezone.now() - timedelta(days=1)
    await force_deck_updated_at(deck.id, past)

    fixed_ts = timezone.now()
    c1 = await make_card(deck, front="c1")
    c2 = await make_card(deck, front="c2")
    c3 = await make_card(deck, front="c3")
    await force_card_updated_at(c1.id, fixed_ts)
    await force_card_updated_at(c2.id, fixed_ts)
    await force_card_updated_at(c3.id, fixed_ts)

    # Sort by id ASC to know the canonical walk order.
    ids_in_order = sorted([c1.id, c2.id, c3.id])
    token = await make_token(alice)

    # First pull (no cursor): all three cards in id order.
    first = await async_client.get(SYNC_URL, headers=bearer(token))
    assert first.status_code == 200
    first_body = first.json()
    returned_first = [
        c["id"] for c in first_body["cards"] if c["id"] in {str(i) for i in ids_in_order}
    ]
    assert returned_first == [str(i) for i in ids_in_order]

    # Now pretend the client only got the FIRST tied row and is asking
    # for "the rest after id = ids_in_order[0]" with the same updated_at.
    # The composite predicate must return ids_in_order[1] and [2] only —
    # no skip past, no duplicate of, the cursor row.
    cursor = _encode_cursor(fixed_ts, "card", ids_in_order[0])
    second = await async_client.get(SYNC_URL, data={"cursor": cursor}, headers=bearer(token))
    assert second.status_code == 200
    second_body = second.json()
    returned_second = [
        c["id"]
        for c in second_body["cards"]
        if c["id"] in {str(i) for i in ids_in_order}
    ]
    assert returned_second == [str(ids_in_order[1]), str(ids_in_order[2])]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_pull_with_latest_cursor_returns_empty(async_client):
    """A client that's already caught up sends back the server_now from
    its previous pull. The next call must surface zero changes — and
    ``has_more`` must be false."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    await make_card(deck)
    token = await make_token(alice)

    first = await async_client.get(SYNC_URL, headers=bearer(token))
    cursor = first.json()["next_cursor"]

    second = await async_client.get(
        SYNC_URL,
        data={"cursor": cursor},
        headers=bearer(token),
    )
    body = second.json()
    assert body["decks"] == []
    assert body["cards"] == []
    assert body["has_more"] is False


# --- 4) Multitenant isolation ---------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_sync_does_not_leak_other_users_data(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob, name="Bobs deck")
    await make_card(bobs_deck, front="Bobs card")
    alice_token = await make_token(alice)

    resp = await async_client.get(SYNC_URL, headers=bearer(alice_token))
    body = resp.json()
    assert body["decks"] == []
    assert body["cards"] == []


# --- 5) has_more + pagination converges -----------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_pagination_with_small_limit_walks_full_history(async_client):
    """Loop pulling with limit=2 until has_more=false; the union of all
    pages equals the full set, with no duplicates and no gaps."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    cards = []
    for i in range(5):
        c = await make_card(deck, front=f"q{i}")
        cards.append(c)
    token = await make_token(alice)

    seen_card_ids: list[str] = []
    cursor = None
    safety = 0
    while True:
        params = {"limit": "2"}
        if cursor is not None:
            params["cursor"] = cursor
        resp = await async_client.get(SYNC_URL, data=params, headers=bearer(token))
        body = resp.json()
        seen_card_ids.extend(c["id"] for c in body["cards"])
        cursor = body["next_cursor"]
        if not body["has_more"]:
            break
        safety += 1
        assert safety < 20, "pagination did not converge"

    # Every card is seen exactly once.
    expected = {str(c.id) for c in cards}
    assert set(seen_card_ids) == expected
    assert len(seen_card_ids) == len(expected)
