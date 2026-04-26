"""Reviews router — async queue + transactional, idempotent submission.

Uses ``transaction=True`` so the test runs against a real Postgres
transaction (default test isolation wraps each test in a savepoint,
which would silently swallow the ``select_for_update`` semantics the
production code depends on).
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
from apps.sync.models import SyncEvent

User = get_user_model()
QUEUE_URL = "/api/reviews/queue"
REVIEW_URL = "/api/reviews"
JSON = "application/json"


# --- async helpers ---------------------------------------------------------

@sync_to_async
def make_user(email: str, password: str = "pw-12345678"):
    return User.objects.create_user(email=email, password=password)


@sync_to_async
def make_deck(user, name: str = "Default"):
    return Deck.objects.create(user=user, name=name)


@sync_to_async
def make_card(deck, **kwargs):
    defaults = {"front": "Q", "back": "A"}
    defaults.update(kwargs)
    return Card.objects.create(deck=deck, **defaults)


@sync_to_async
def make_token(user) -> str:
    return str(RefreshToken.for_user(user).access_token)


@sync_to_async
def get_card(card_id):
    return Card.objects.get(id=card_id)


@sync_to_async
def count_reviews_for(card_id) -> int:
    return Review.objects.filter(card_id=card_id).count()


@sync_to_async
def first_review_for(card_id):
    return Review.objects.filter(card_id=card_id).first()


@sync_to_async
def get_sync_event(event_id):
    return SyncEvent.objects.get(id=event_id)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def review_body(card_id, **overrides) -> dict:
    """Build a POST /reviews body with sane defaults for the Bloco 9 fields.

    Tests that need to drive specific idempotency behavior pass overrides
    (notably ``client_event_id`` and ``rating``) explicitly.
    """
    body = {
        "card_id": str(card_id),
        "rating": "good",
        "duration_ms": 4200,
        "client_event_id": str(uuid.uuid4()),
        "device_id": "test-device-1",
        "client_ts": timezone.now().isoformat(),
    }
    body.update(overrides)
    return body


# === GET /queue ============================================================

# --- auth ------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_without_token_returns_401(async_client):
    resp = await async_client.get(
        f"{QUEUE_URL}?deck_id=00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 401


# --- happy path ------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_returns_due_cards_ordered_by_oldest_first(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    now = timezone.now()
    c_oldest = await make_card(deck, front="oldest", due_at=now - timedelta(days=5))
    c_mid = await make_card(deck, front="mid", due_at=now - timedelta(days=2))
    c_youngest = await make_card(deck, front="youngest", due_at=now - timedelta(hours=1))
    token = await make_token(alice)

    resp = await async_client.get(
        f"{QUEUE_URL}?deck_id={deck.id}", headers=bearer(token)
    )

    assert resp.status_code == 200
    body = resp.json()
    assert [c["front"] for c in body] == ["oldest", "mid", "youngest"]
    ids = {c["id"] for c in body}
    assert ids == {str(c_oldest.id), str(c_mid.id), str(c_youngest.id)}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_excludes_cards_due_in_the_future(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    now = timezone.now()
    due = await make_card(deck, front="due", due_at=now - timedelta(days=1))
    await make_card(deck, front="future", due_at=now + timedelta(days=3))
    token = await make_token(alice)

    resp = await async_client.get(
        f"{QUEUE_URL}?deck_id={deck.id}", headers=bearer(token)
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == str(due.id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_respects_limit_param(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    now = timezone.now()
    for i in range(5):
        await make_card(deck, front=f"q{i}", due_at=now - timedelta(days=i + 1))
    token = await make_token(alice)

    resp = await async_client.get(
        f"{QUEUE_URL}?deck_id={deck.id}&limit=2", headers=bearer(token)
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_rejects_limit_above_max(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    token = await make_token(alice)

    resp = await async_client.get(
        f"{QUEUE_URL}?deck_id={deck.id}&limit=500", headers=bearer(token)
    )

    assert resp.status_code == 422


# --- isolation -------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_of_other_users_deck_returns_empty(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob)
    await make_card(bobs_deck, due_at=timezone.now() - timedelta(days=1))
    alice_token = await make_token(alice)

    resp = await async_client.get(
        f"{QUEUE_URL}?deck_id={bobs_deck.id}", headers=bearer(alice_token)
    )

    assert resp.status_code == 200
    assert resp.json() == []


# === POST /reviews =========================================================

# --- auth ------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_review_without_token_returns_401(async_client):
    resp = await async_client.post(REVIEW_URL, data={}, content_type=JSON)
    assert resp.status_code == 401


# --- payload validation ----------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_review_with_invalid_rating_returns_422(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck)
    token = await make_token(alice)

    resp = await async_client.post(
        REVIEW_URL,
        data=review_body(card.id, rating="perfect"),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 422


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_review_with_negative_duration_returns_422(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck)
    token = await make_token(alice)

    resp = await async_client.post(
        REVIEW_URL,
        data=review_body(card.id, duration_ms=-10),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 422


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_review_missing_idempotency_fields_returns_422(async_client):
    """The 3 Bloco 9 fields are required — old clients sending only
    {card_id, rating, duration_ms} must be rejected, not silently accepted."""
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(deck)
    token = await make_token(alice)

    resp = await async_client.post(
        REVIEW_URL,
        data={"card_id": str(card.id), "rating": "good", "duration_ms": 100},
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 422


# --- happy path: card mutated, review row created -------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_good_review_updates_card_and_creates_review_row(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(
        deck,
        front="Capital of France",
        back="Paris",
        state="review",
        ease_factor=2.5,
        interval_days=10,
        repetitions=3,
        due_at=timezone.now() - timedelta(days=1),
    )
    token = await make_token(alice)
    before = timezone.now()

    resp = await async_client.post(
        REVIEW_URL,
        data=review_body(card.id, rating="good", duration_ms=4200),
        content_type=JSON,
        headers=bearer(token),
    )
    after = timezone.now()

    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "review"
    assert body["id"] == str(card.id)

    refreshed = await get_card(card.id)
    assert refreshed.state == "review"
    assert refreshed.interval_days == 25
    assert refreshed.repetitions == 4
    assert refreshed.ease_factor == pytest.approx(2.5)
    expected_low = before + timedelta(days=25)
    expected_high = after + timedelta(days=25)
    assert expected_low <= refreshed.due_at <= expected_high

    assert await count_reviews_for(card.id) == 1
    review = await first_review_for(card.id)
    assert review.rating == "good"
    assert review.prev_interval == 10
    assert review.new_interval == 25
    assert review.duration_ms == 4200


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_again_review_lapses_a_review_card(async_client):
    alice = await make_user("alice@example.com")
    deck = await make_deck(alice)
    card = await make_card(
        deck,
        state="review",
        ease_factor=2.0,
        interval_days=20,
        repetitions=5,
        due_at=timezone.now() - timedelta(days=1),
    )
    token = await make_token(alice)

    resp = await async_client.post(
        REVIEW_URL,
        data=review_body(card.id, rating="again", duration_ms=8000),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 200
    refreshed = await get_card(card.id)
    assert refreshed.state == "lapsed"
    assert refreshed.interval_days == 0
    assert refreshed.repetitions == 0
    assert refreshed.ease_factor == pytest.approx(1.70)


# --- isolation -------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_review_for_other_users_card_returns_404(async_client):
    alice = await make_user("alice@example.com")
    bob = await make_user("bob@example.com")
    bobs_deck = await make_deck(bob)
    bobs_card = await make_card(
        bobs_deck,
        state="review",
        ease_factor=2.5,
        interval_days=10,
        repetitions=3,
    )
    alice_token = await make_token(alice)

    resp = await async_client.post(
        REVIEW_URL,
        data=review_body(bobs_card.id, rating="good", duration_ms=1000),
        content_type=JSON,
        headers=bearer(alice_token),
    )

    assert resp.status_code == 404
    refreshed = await get_card(bobs_card.id)
    assert refreshed.interval_days == 10
    assert refreshed.repetitions == 3
    assert await count_reviews_for(bobs_card.id) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_review_for_nonexistent_card_returns_404(async_client):
    alice = await make_user("alice@example.com")
    token = await make_token(alice)

    resp = await async_client.post(
        REVIEW_URL,
        data=review_body("00000000-0000-0000-0000-000000000000"),
        content_type=JSON,
        headers=bearer(token),
    )

    assert resp.status_code == 404


# === Bloco 9: idempotency contract =========================================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_idempotent_replay_returns_same_response_and_mutates_card_once(
    async_client,
):
    """Same client_event_id submitted twice -> 200 both, identical body,
    Card mutated exactly once, Review row inserted exactly once, and the
    SyncEvent envelope holds both the request and the result."""
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

    # Build the body ONCE so client_event_id and client_ts are identical
    # across both calls — that's exactly what an HTTP retry on a flaky
    # 4G connection looks like.
    body = review_body(card.id, rating="good", duration_ms=4200)

    r1 = await async_client.post(
        REVIEW_URL, data=body, content_type=JSON, headers=bearer(token)
    )
    r2 = await async_client.post(
        REVIEW_URL, data=body, content_type=JSON, headers=bearer(token)
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    # Byte-identical replay: the second response is the saved snapshot,
    # not a fresh computation. due_at, repetitions, etc. all match.
    assert r1.json() == r2.json()

    # Card was mutated once: 10 -> 25 (good), not 10 -> 25 -> 62.
    refreshed = await get_card(card.id)
    assert refreshed.interval_days == 25
    assert refreshed.repetitions == 4

    # Exactly one Review row, not two.
    assert await count_reviews_for(card.id) == 1

    # SyncEvent stored both halves of the envelope.
    event = await get_sync_event(body["client_event_id"])
    assert event.status == "applied"
    assert event.payload["request"]["rating"] == "good"
    assert event.payload["result"]["state"] == "review"
    assert event.payload["result"]["id"] == str(card.id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reusing_event_id_with_different_rating_returns_409(async_client):
    """Same client_event_id but a different rating -> 409, and the card
    keeps the state from the original (winning) call."""
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

    shared_event_id = str(uuid.uuid4())
    shared_ts = timezone.now().isoformat()

    r1 = await async_client.post(
        REVIEW_URL,
        data=review_body(
            card.id,
            rating="good",
            duration_ms=4200,
            client_event_id=shared_event_id,
            client_ts=shared_ts,
        ),
        content_type=JSON,
        headers=bearer(token),
    )
    assert r1.status_code == 200

    r2 = await async_client.post(
        REVIEW_URL,
        data=review_body(
            card.id,
            rating="again",  # different from r1's "good"
            duration_ms=4200,
            client_event_id=shared_event_id,  # but same key
            client_ts=shared_ts,
        ),
        content_type=JSON,
        headers=bearer(token),
    )
    assert r2.status_code == 409
    assert r2.json()["detail"] == "idempotency_key_reused"

    # Card kept the 'good' outcome — 'again' was REFUSED, not applied.
    refreshed = await get_card(card.id)
    assert refreshed.state == "review"
    assert refreshed.interval_days == 25
    assert refreshed.repetitions == 4
    # Only the original Review row exists.
    assert await count_reviews_for(card.id) == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_distinct_event_ids_apply_independently(async_client):
    """Sanity check that idempotency dedupes on the KEY, not on payload
    similarity — two reviews of the same card with the same rating but
    different client_event_ids must both apply."""
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

    r1 = await async_client.post(
        REVIEW_URL,
        data=review_body(card.id, rating="good"),
        content_type=JSON,
        headers=bearer(token),
    )
    r2 = await async_client.post(
        REVIEW_URL,
        data=review_body(card.id, rating="good"),
        content_type=JSON,
        headers=bearer(token),
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    # Two distinct rating events => SM-2 ran twice, two Review rows.
    assert await count_reviews_for(card.id) == 2
    refreshed = await get_card(card.id)
    # repetitions: 3 -> 4 -> 5, interval: 10 -> 25 -> 62 (round(25*2.5)).
    assert refreshed.repetitions == 5
    assert refreshed.interval_days == 62
