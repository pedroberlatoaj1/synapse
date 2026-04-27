"""Sync push (POST /sync) — LWW resolution, tiebreaker, multitenant.

``transaction=True`` so ``select_for_update`` and the advisory lock
operate on real Postgres transactions instead of the savepoint that
the default test isolation would wrap them in.
"""
import uuid
from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja_jwt.tokens import RefreshToken

from apps.decks.models import Card, Deck
from apps.reviews.models import Review

User = get_user_model()
PUSH_URL = "/api/sync"
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
def stamp_card_lww(card_id, ts, event_id):
    Card.objects.filter(id=card_id).update(
        last_client_ts=ts, last_event_id=event_id
    )


@sync_to_async
def stamp_deck_lww(deck_id, ts, event_id):
    Deck.objects.filter(id=deck_id).update(
        last_client_ts=ts, last_event_id=event_id
    )


@sync_to_async
def get_card(card_id):
    return Card.objects.get(id=card_id)


@sync_to_async
def get_deck(deck_id):
    return Deck.objects.get(id=deck_id)


@sync_to_async
def deck_exists(deck_id) -> bool:
    return Deck.objects.filter(id=deck_id).exists()


@sync_to_async
def count_reviews_for(card_id) -> int:
    return Review.objects.filter(card_id=card_id).count()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def push_body(events: list[dict], device_id: str = "iphone-1") -> dict:
    return {"device_id": device_id, "events": events}


def make_event(
    *,
    op: str,
    entity_type: str,
    entity_id,
    payload: dict,
    client_ts=None,
    event_id=None,
) -> dict:
    return {
        "id": str(event_id or uuid.uuid4()),
        "op": op,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "client_ts": (client_ts or timezone.now()).isoformat(),
        "payload": payload,
    }


# === 1) Auth ===============================================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_push_without_token_returns_401(async_client):
    resp = await async_client.post(
        PUSH_URL, data=push_body([]), content_type=JSON
    )
    assert resp.status_code == 401


# === 2) LWW basic: stale event loses ======================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_event_with_stale_client_ts_is_rejected_as_conflict(
    async_client,
):
    """Server has card stamped at T=100. Incoming update at T=99 must
    be rejected as ``stale_event`` and the card stays untouched."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="server-front")

    server_ts = timezone.now()
    server_event = uuid.uuid4()
    await stamp_card_lww(card.id, server_ts, server_event)

    stale_ts = server_ts - timedelta(seconds=10)
    token = await make_token(alice)

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"front": "client-tried-to-overwrite"},
                    client_ts=stale_ts,
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == []
    assert len(body["conflicts"]) == 1
    conflict = body["conflicts"][0]
    assert conflict["reason"] == "stale_event"
    assert conflict["server_state"]["front"] == "server-front"

    # Server state unchanged.
    refreshed = await get_card(card.id)
    assert refreshed.front == "server-front"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_event_with_newer_client_ts_is_applied(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="old")

    server_ts = timezone.now() - timedelta(seconds=10)
    await stamp_card_lww(card.id, server_ts, uuid.uuid4())
    token = await make_token(alice)

    new_ts = timezone.now()
    new_event = uuid.uuid4()

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"front": "new-front"},
                    client_ts=new_ts,
                    event_id=new_event,
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert str(new_event) in body["accepted"]
    assert body["conflicts"] == []

    refreshed = await get_card(card.id)
    assert refreshed.front == "new-front"
    assert refreshed.last_event_id == new_event


# === 3) LWW tiebreaker on identical client_ts =============================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_tied_client_ts_with_smaller_event_id_loses(async_client):
    """Same exact client_ts as the server's stamp; tiebreaker is the
    UUID. The smaller-id event must lose."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="server-front")
    token = await make_token(alice)

    fixed_ts = timezone.now()
    # Pick a server event id that is HIGHER than the incoming one so
    # the tiebreaker forces the rejection regardless of UUID4 luck.
    server_event = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    incoming_event = uuid.UUID("00000000-0000-0000-0000-000000000001")
    await stamp_card_lww(card.id, fixed_ts, server_event)

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"front": "should-not-stick"},
                    client_ts=fixed_ts,
                    event_id=incoming_event,
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == []
    assert len(body["conflicts"]) == 1
    assert body["conflicts"][0]["reason"] == "stale_event"

    refreshed = await get_card(card.id)
    assert refreshed.front == "server-front"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_tied_client_ts_with_larger_event_id_wins(async_client):
    """Mirror image: identical client_ts, but the incoming event id is
    lexicographically GREATER than the server's, so it wins."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="server-front")
    token = await make_token(alice)

    fixed_ts = timezone.now()
    server_event = uuid.UUID("00000000-0000-0000-0000-000000000001")
    incoming_event = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    await stamp_card_lww(card.id, fixed_ts, server_event)

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"front": "winner"},
                    client_ts=fixed_ts,
                    event_id=incoming_event,
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert str(incoming_event) in body["accepted"]
    refreshed = await get_card(card.id)
    assert refreshed.front == "winner"


# === 4) Multitenant isolation =============================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_targeting_another_users_entity_returns_conflict_no_leak(
    async_client,
):
    """Bob tries to push an update referencing Alice's card. The server
    must surface a conflict (entity_not_found) without leaking Alice's
    card content via ``server_state``."""
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    alices_deck = await make_deck(alice)
    alices_card = await make_card(
        alices_deck, front="alice secret"
    )
    bob_token = await make_token(bob)

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=alices_card.id,
                    payload={"front": "hijacked"},
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(bob_token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == []
    assert len(body["conflicts"]) == 1
    conflict = body["conflicts"][0]
    assert conflict["reason"] == "entity_not_found"
    # No server_state echoed — Bob must not learn ANYTHING about Alice's row.
    assert conflict["server_state"] is None
    body_str = str(body)
    assert "alice secret" not in body_str

    # Alice's card is untouched.
    refreshed = await get_card(alices_card.id)
    assert refreshed.front == "alice secret"


# === 5) Idempotent retries ================================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_replaying_same_event_id_does_not_double_apply(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="initial")
    token = await make_token(alice)

    event_id = uuid.uuid4()
    body = push_body(
        [
            make_event(
                op="update",
                entity_type="card",
                entity_id=card.id,
                payload={"front": "v1"},
                event_id=event_id,
            )
        ]
    )

    r1 = await async_client.post(
        PUSH_URL, data=body, content_type=JSON, headers=bearer(token)
    )
    r2 = await async_client.post(
        PUSH_URL, data=body, content_type=JSON, headers=bearer(token)
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert str(event_id) in r1.json()["accepted"]
    # Second request also reports accepted (transparent replay) but no
    # second mutation happens — front stays "v1", not bouncing or
    # vanishing.
    assert str(event_id) in r2.json()["accepted"]
    refreshed = await get_card(card.id)
    assert refreshed.front == "v1"


# === 6) op=create =========================================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_deck_event_creates_deck_owned_by_user(async_client):
    alice = await make_user("alice@example.com")
    token = await make_token(alice)
    new_deck_id = uuid.uuid4()
    create_evt = uuid.uuid4()

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="create",
                    entity_type="deck",
                    entity_id=new_deck_id,
                    payload={"name": "Created via sync", "description": "hi"},
                    event_id=create_evt,
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    # accepted carries the EVENT id, not the entity id.
    assert str(create_evt) in resp.json()["accepted"]

    deck = await get_deck(new_deck_id)
    assert deck.user_id == alice.id
    assert deck.name == "Created via sync"


# === 7) op=delete cascades ================================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_deck_event_soft_deletes_deck_and_its_cards(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck)
    token = await make_token(alice)

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="delete",
                    entity_type="deck",
                    entity_id=deck.id,
                    payload={},
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    assert resp.json()["conflicts"] == []

    refreshed_deck = await get_deck(deck.id)
    refreshed_card = await get_card(card.id)
    assert refreshed_deck.deleted_at is not None
    assert refreshed_card.deleted_at is not None


# === 8) op=review goes through SM-2 =======================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_review_event_via_push_runs_sm2_and_logs_review(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(
        deck,
        state="review",
        ease_factor=2.5,
        interval_days=10,
        repetitions=3,
        due_at=timezone.now() - timedelta(days=1),
    )
    token = await make_token(alice)

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="review",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"rating": "good", "duration_ms": 4200},
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    assert resp.json()["conflicts"] == []

    refreshed = await get_card(card.id)
    assert refreshed.interval_days == 25  # 10 * 2.5 = 25
    assert refreshed.repetitions == 4
    assert await count_reviews_for(card.id) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_review_event_with_stale_client_ts_is_rejected(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(
        deck,
        state="review",
        ease_factor=2.5,
        interval_days=10,
        repetitions=3,
        due_at=timezone.now() - timedelta(days=1),
    )
    server_ts = timezone.now()
    await stamp_card_lww(card.id, server_ts, uuid.uuid4())
    token = await make_token(alice)

    stale_ts = server_ts - timedelta(seconds=5)
    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="review",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"rating": "again", "duration_ms": 1000},
                    client_ts=stale_ts,
                )
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] == []
    assert len(body["conflicts"]) == 1
    assert body["conflicts"][0]["reason"] == "stale_event"

    # Card SM-2 fields untouched, no Review row inserted.
    refreshed = await get_card(card.id)
    assert refreshed.interval_days == 10
    assert refreshed.repetitions == 3
    assert await count_reviews_for(card.id) == 0


# === 9) Mixed batch =======================================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mixed_batch_partitions_results(async_client):
    """One create (ok), one update (ok), one stale update (conflict)
    in the same batch — the response reports each independently."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck, front="initial")

    # Stamp the card so the stale event has something to lose against.
    server_ts = timezone.now()
    await stamp_card_lww(card.id, server_ts, uuid.uuid4())
    token = await make_token(alice)

    new_deck_id = uuid.uuid4()
    create_evt = uuid.uuid4()
    update_evt = uuid.uuid4()
    stale_evt = uuid.uuid4()

    resp = await async_client.post(
        PUSH_URL,
        data=push_body(
            [
                make_event(
                    op="create",
                    entity_type="deck",
                    entity_id=new_deck_id,
                    payload={"name": "fresh"},
                    event_id=create_evt,
                ),
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"front": "newer"},
                    client_ts=server_ts + timedelta(seconds=1),
                    event_id=update_evt,
                ),
                make_event(
                    op="update",
                    entity_type="card",
                    entity_id=card.id,
                    payload={"front": "stale"},
                    client_ts=server_ts - timedelta(seconds=1),
                    event_id=stale_evt,
                ),
            ]
        ),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    accepted = set(body["accepted"])
    conflict_ids = {c["event_id"] for c in body["conflicts"]}
    assert {str(create_evt), str(update_evt)} <= accepted
    assert str(stale_evt) in conflict_ids

    # Final card state is the WINNER's, not the stale one.
    refreshed = await get_card(card.id)
    assert refreshed.front == "newer"
    assert await deck_exists(new_deck_id)
