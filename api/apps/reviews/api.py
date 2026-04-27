"""Reviews router — async queue + idempotent transactional review submission.

The two endpoints have very different concurrency profiles:

* ``GET /reviews/queue`` is a read-only point-in-time snapshot of due
  cards. Single SELECT, no lock, no transaction — runs natively async.

* ``POST /reviews`` mutates two tables (Card update + Review insert)
  and must be both atomic AND idempotent. Django 5.2's
  ``transaction.atomic`` is still a sync context manager bound to the
  current thread's DB connection, so we cannot open it from inside
  ``async def`` without risking the block running on a thread that
  doesn't own the connection. The fix: pack the whole transactional
  sequence into a sync helper (``_apply_review_tx``) and dispatch it
  via ``sync_to_async(..., thread_sensitive=True)`` — that pins the
  work to the request's thread, keeps the atomic block coherent, and
  makes the lock and the rows it covers move together.

Bloco 9 — strict idempotency
----------------------------
Every POST /reviews carries a client-generated ``client_event_id``
(UUID v4/v7). The server uses it as the primary key of a
``SyncEvent`` row and treats that row as the authoritative dedupe
record:

1. We try a single raw INSERT ... ON CONFLICT (id) DO NOTHING
   RETURNING id. The PK conflict path is atomic at the storage layer
   — two concurrent retries cannot both win.
2. If the INSERT returned an id we are the *winner*: run the SM-2
   transaction normally, then update the SyncEvent's payload with the
   computed ``CardOut`` snapshot so future retries can replay it.
3. If the INSERT returned no row we are the *loser*: another request
   already claimed the key. We re-read the SyncEvent under
   ``SELECT ... FOR UPDATE`` so we wait for the winner's transaction
   to commit (otherwise we'd see a half-written envelope), then:
   - if the saved request matches ours, return the saved result
     (transparent retry replay);
   - if it differs, raise ``IdempotencyKeyReused`` -> 409 (the same
     key was reused with a different payload, which is a client bug
     or replay attack — never silently overwrite).

Why ``select_for_update`` on the Card stays inside the winner path:
two devices of the same user replaying offline reviews can submit
ratings for *different* cards using the same card's id. Without a row
lock on Card, both reads see the same ``state`` and write back
conflicting next-states. FOR UPDATE serializes them at the Postgres
level so each rating is applied to the freshest state.
"""
from __future__ import annotations

import json
import uuid
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.db import connection, transaction
from django.utils import timezone
from ninja import Query, Router
from ninja.responses import Status

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Card
from apps.decks.schemas import CardOut
from apps.reviews.models import Review
from apps.reviews.schemas import ReviewIn
from apps.reviews.sm2 import calculate_next_state
from apps.sync.models import SyncEvent

router = Router(auth=AsyncJWTAuth(), tags=["Reviews"])


# --- GET /queue ------------------------------------------------------------

@router.get("/queue", response=list[CardOut])
async def queue(
    request,
    deck_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
):
    """Return cards in the deck that are due (due_at <= now), oldest first.

    The deck__user filter is what enforces multitenant isolation: a
    foreign deck_id yields an empty list rather than a 404 — the API
    treats "not your deck" identically to "your deck has nothing due"
    so attackers cannot probe for deck existence by timing or shape.
    """
    now = timezone.now()
    qs = (
        Card.objects.filter(
            deck_id=deck_id,
            user=request.user,
            deck__deleted_at__isnull=True,
            due_at__lte=now,
            deleted_at__isnull=True,
        )
        .order_by("due_at")
        .values("id", "deck_id", "front", "back", "state", "due_at")[:limit]
    )
    return [card async for card in qs]


# --- POST / (submit a review) ---------------------------------------------


class IdempotencyKeyReused(Exception):
    """Raised when a client_event_id is reused with a different request.

    Maps to HTTP 409 in the async handler. We never overwrite the
    original outcome — refusing the second call is the only safe move
    if the bodies disagree.
    """


def _serialize_request(payload: ReviewIn) -> dict:
    """Stable, JSON-friendly snapshot of the incoming request.

    UUIDs and datetimes are coerced to strings so the dict round-trips
    through JSONField storage and equality comparison stays cheap and
    deterministic.
    """
    return {
        "card_id": str(payload.card_id),
        "rating": payload.rating,
        "duration_ms": payload.duration_ms,
        "client_event_id": str(payload.client_event_id),
        "device_id": payload.device_id,
        "client_ts": payload.client_ts.isoformat(),
    }


def _serialize_card_out(card: Card) -> dict:
    """JSON-friendly snapshot of the response we'll replay on retry."""
    return {
        "id": str(card.id),
        "deck_id": str(card.deck_id),
        "front": card.front,
        "back": card.back,
        "state": card.state,
        "due_at": card.due_at.isoformat(),
    }


def _apply_review_tx(*, payload: ReviewIn, user_id: int) -> dict:
    """Sync transactional core of POST /reviews — idempotent via SyncEvent.

    See module docstring for the full idempotency contract. Raises
    ``Card.DoesNotExist`` (winner path) for missing/foreign card, and
    ``IdempotencyKeyReused`` (loser path) for replay-with-different-body.
    """
    request_snapshot = _serialize_request(payload)
    initial_envelope = {"request": request_snapshot, "result": None}

    with transaction.atomic():
        # --- 1. Atomic dedupe via raw SQL on the PK. -----------------------
        # Using a raw cursor instead of ORM .create() because Django's
        # bulk_create + ignore_conflicts won't return whether THIS row
        # was the inserted one, and we need that signal to branch. The
        # PK conflict path is fully atomic at storage level — two
        # concurrent retries cannot both come out as winners.
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sync_syncevent
                    (id, user_id, device_id, entity_type, entity_id,
                     op, payload, client_ts, server_ts, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, NOW(), %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
                """,
                [
                    str(payload.client_event_id),
                    user_id,
                    payload.device_id,
                    "card",
                    str(payload.card_id),
                    "review",
                    json.dumps(initial_envelope),
                    payload.client_ts,
                    "pending",
                ],
            )
            inserted = cursor.fetchone()

        if inserted is None:
            # --- 2. Loser path: row already existed. -----------------------
            # SELECT FOR UPDATE blocks until the winner's tx commits, so
            # we never read a half-applied envelope. Filtering by user_id
            # keeps the dedupe space scoped — a stolen key from another
            # user surfaces as a conflict rather than leaking that the id
            # was used elsewhere.
            try:
                existing = SyncEvent.objects.select_for_update().get(
                    id=payload.client_event_id, user_id=user_id
                )
            except SyncEvent.DoesNotExist as exc:
                raise IdempotencyKeyReused() from exc

            stored_envelope = existing.payload or {}
            if stored_envelope.get("request") != request_snapshot:
                # Same key, different body: never overwrite. The original
                # outcome is the only safe answer; force the client to
                # pick a new key.
                raise IdempotencyKeyReused()

            stored_result = stored_envelope.get("result")
            if stored_result is None:
                # Defensive: post-commit the result is always populated;
                # a None here means we lost a race against a winner that
                # rolled back (e.g. Card.DoesNotExist). Treating it as a
                # conflict is safer than re-running with stale state.
                raise IdempotencyKeyReused()

            return stored_result

        # --- 3. Winner path: apply SM-2 + persist Review + finalize. -------
        # Lock the row before reading SM-2 fields. Two concurrent reviews
        # on the same card now serialize at this point. Soft-deleted
        # cards are invisible — reviewing a tombstone is meaningless.
        card = Card.objects.select_for_update().get(
            id=payload.card_id,
            user_id=user_id,
            deck__deleted_at__isnull=True,
            deleted_at__isnull=True,
        )

        prev_interval = card.interval_days
        next_state = calculate_next_state(
            state=card.state,
            ease_factor=card.ease_factor,
            interval_days=card.interval_days,
            repetitions=card.repetitions,
            rating=payload.rating,
        )
        new_due_at = timezone.now() + timedelta(days=next_state["interval_days"])

        card.state = next_state["state"]
        card.ease_factor = next_state["ease_factor"]
        card.interval_days = next_state["interval_days"]
        card.repetitions = next_state["repetitions"]
        card.due_at = new_due_at
        # Stamp the LWW signature so the next sync push sees this client
        # event as the "current" baseline. Online POST /reviews is the
        # authoritative source-of-truth for the moment it happens, so
        # we don't run the LWW comparison here — the sync push wrapper
        # does that for replayed offline events before delegating.
        card.last_client_ts = payload.client_ts
        card.last_event_id = payload.client_event_id
        card.save(
            update_fields=[
                "state",
                "ease_factor",
                "interval_days",
                "repetitions",
                "due_at",
                "updated_at",
                "last_client_ts",
                "last_event_id",
            ]
        )

        Review.objects.create(
            card=card,
            user_id=user_id,
            rating=payload.rating,
            prev_interval=prev_interval,
            new_interval=next_state["interval_days"],
            duration_ms=payload.duration_ms,
        )

        # Finalize the SyncEvent with the response snapshot so retries
        # have something to replay. Status flips from 'pending' to
        # 'applied' once the full transaction succeeds.
        result_snapshot = _serialize_card_out(card)
        SyncEvent.objects.filter(id=payload.client_event_id).update(
            payload={"request": request_snapshot, "result": result_snapshot},
            status="applied",
        )

        return result_snapshot


@router.post("", response={200: CardOut, 404: dict, 409: dict})
async def submit_review(request, payload: ReviewIn):
    try:
        data = await sync_to_async(_apply_review_tx, thread_sensitive=True)(
            payload=payload, user_id=request.user.id
        )
    except Card.DoesNotExist:
        # 404 — never 403 — for the same enumeration-protection reason
        # as decks/cards: don't leak that the id exists but isn't yours.
        return Status(404, {"detail": "Card not found"})
    except IdempotencyKeyReused:
        return Status(409, {"detail": "idempotency_key_reused"})

    return Status(200, CardOut(**data))
