"""Reviews router — async queue + idempotent, LWW-checked review submission.

The two endpoints have very different concurrency profiles:

* ``GET /reviews/queue`` is a read-only point-in-time snapshot of due
  cards. Single SELECT, no lock, no transaction — runs natively async.

* ``POST /reviews`` mutates two tables (Card update + Review insert)
  under three coordinated guarantees: idempotency on retry, LWW on
  out-of-order replay, and atomicity of the SM-2 + Review row write.
  Django 5.2's ``transaction.atomic`` is still a sync context manager
  bound to the current thread's DB connection, so we cannot open it
  from inside ``async def`` without risking the block running on a
  thread that doesn't own the connection. The fix: pack the whole
  transactional sequence into ``_apply_review_tx`` and dispatch it via
  ``sync_to_async(..., thread_sensitive=True)`` — that pins the work
  to the request's thread, keeps the atomic block coherent, and makes
  the lock and the rows it covers move together.

Single-transaction guarantee (Bloco 11 P0 fix)
----------------------------------------------
Every review now runs ALL of these inside one ``transaction.atomic()``:

1. Acquire ``pg_advisory_xact_lock`` on ``(user_id, card_id)`` so two
   concurrent reviewers (online retry, offline replay, two devices)
   serialize at this one point. The lock is released on commit/rollback.
2. ``INSERT ... ON CONFLICT (id) DO NOTHING`` against ``sync_syncevent``
   to claim the idempotency key, with the row stamped ``status='pending'``
   until we know the outcome.
3. ``select_for_update`` the Card.
4. Compare ``(payload.client_ts, payload.client_event_id)`` against
   ``(card.last_client_ts, card.last_event_id)``. If the incoming pair
   is not strictly newer, persist the SyncEvent as ``status='conflict'``
   with the server_state and return the conflict tuple — retries replay
   that conflict instead of re-running the math.
5. If LWW wins: apply SM-2, write the Review row, stamp the Card with
   the new LWW signature, and persist the SyncEvent as ``status='applied'``
   with the response snapshot so future retries get a byte-identical
   replay.

Previous design held the lock + ran LWW in one transaction, then
released the lock and called a second transaction to apply SM-2 — a
classic TOCTOU window where a competing writer could interleave between
the two. The audit caught this and rolled it into the consolidation
above.

SyncEvent state machine (Bloco 11 P1 fix)
------------------------------------------
* ``pending`` — transient state inside the active transaction; never
  observed post-commit (the same transaction always flips it to
  ``applied`` or ``conflict`` before commit).
* ``applied`` — SM-2 ran, Card mutated, Review row inserted.
  ``payload.result`` carries the response snapshot.
* ``conflict`` — LWW rejected the event. ``payload.conflict`` carries
  ``{reason, server_state}``.

On retry, the loser path takes ``SELECT FOR UPDATE`` on the existing
SyncEvent (which blocks until the original transaction commits), checks
the saved request matches the incoming one (otherwise: 409, never
overwrite), then replays the saved outcome — accepted or conflict
exactly as the original call returned.
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
from apps.sync.lww import lww_loses, serialize_card_state
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
    """Raised when a client_event_id is reused with a different request,
    or when the id was burned by another user. Maps to HTTP 409.
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


def _apply_review_tx(*, payload: ReviewIn, user_id: int) -> tuple[str, dict]:
    """Sync, transactional, idempotent, LWW-checked review submission.

    Returns one of:
        ``("accepted", card_out_dict)``
            SM-2 applied, Card mutated, Review row inserted, SyncEvent
            finalized with status=applied. The dict is a CardOut snapshot.
        ``("conflict", details_dict)``
            LWW rejected the event as stale. SyncEvent finalized with
            status=conflict and the same details. ``details_dict`` carries
            ``{"reason": "stale_event", "server_state": {...card snapshot...}}``.

    Raises:
        Card.DoesNotExist — card missing or owned by another user.
            The whole transaction (including the SyncEvent INSERT) rolls
            back so retries re-run the lookup, not a stale replay.
        IdempotencyKeyReused — same client_event_id seen with a different
            request body, OR the key is owned by another user.
    """
    request_snapshot = _serialize_request(payload)
    initial_envelope = {"request": request_snapshot, "result": None, "conflict": None}

    with transaction.atomic():
        # 1. Advisory lock on (user, card) — serializes every path that
        # could mutate this card across both /reviews and /sync push.
        # Held for the lifetime of this transaction; released on commit.
        with connection.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                [f"{user_id}:{payload.card_id}"],
            )

        # 2. Atomic dedupe via PK conflict. The row goes in as 'pending'
        # so a crash between INSERT and the final UPDATE leaves no
        # half-applied state visible to retries (the transaction would
        # have rolled back anyway).
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
            # --- Replay path: a previous request already claimed the key. -
            # SELECT FOR UPDATE blocks until the original tx commits, so
            # status is always terminal (applied|conflict) by the time we
            # read it. user_id scoping keeps the dedupe space per-tenant.
            try:
                existing = SyncEvent.objects.select_for_update().get(
                    id=payload.client_event_id, user_id=user_id
                )
            except SyncEvent.DoesNotExist as exc:
                raise IdempotencyKeyReused() from exc

            stored = existing.payload or {}
            if stored.get("request") != request_snapshot:
                # Same key, different body: never overwrite the original
                # outcome. Force the client onto a new key.
                raise IdempotencyKeyReused()

            if existing.status == "applied":
                # Replay the original success snapshot byte-identically.
                return ("accepted", stored.get("result") or {})
            if existing.status == "conflict":
                # Replay the original LWW rejection so the client sees
                # the same conflict on every retry, not a fresh check
                # against (potentially) further-mutated server state.
                return (
                    "conflict",
                    stored.get("conflict") or {"reason": "stale_event"},
                )
            # 'pending' is impossible post-commit — defensive: treat as
            # reuse rather than re-running with stale state.
            raise IdempotencyKeyReused()

        # --- Winner path: claim the row and process. ----------------------
        # Lookup before LWW so a missing/foreign card surfaces as 404
        # (rolled back along with the SyncEvent INSERT). Soft-deleted
        # cards are invisible — reviewing a tombstone is meaningless.
        card = Card.objects.select_for_update().get(
            id=payload.card_id,
            user_id=user_id,
            deck__deleted_at__isnull=True,
            deleted_at__isnull=True,
        )

        if lww_loses(
            payload.client_ts,
            payload.client_event_id,
            card.last_client_ts,
            card.last_event_id,
        ):
            # 3. LWW rejected: persist the conflict so retries replay it,
            # then return the conflict tuple. We DO NOT raise here — the
            # SyncEvent UPDATE must commit alongside the (unchanged) Card
            # state so the next retry of this exact event id finds the
            # frozen rejection.
            conflict_details = {
                "reason": "stale_event",
                "server_state": serialize_card_state(card),
            }
            SyncEvent.objects.filter(id=payload.client_event_id).update(
                payload={
                    "request": request_snapshot,
                    "result": None,
                    "conflict": conflict_details,
                },
                status="conflict",
            )
            return ("conflict", conflict_details)

        # 4. LWW won: apply SM-2 to the locked card.
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
        # Stamp the LWW signature so the next push event sees this client
        # event as the "current" baseline.
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

        # 5. Finalize: applied + result snapshot for retry replay.
        result_snapshot = _serialize_card_out(card)
        SyncEvent.objects.filter(id=payload.client_event_id).update(
            payload={
                "request": request_snapshot,
                "result": result_snapshot,
                "conflict": None,
            },
            status="applied",
        )
        return ("accepted", result_snapshot)


@router.post("", response={200: CardOut, 404: dict, 409: dict})
async def submit_review(request, payload: ReviewIn):
    try:
        outcome, details = await sync_to_async(
            _apply_review_tx, thread_sensitive=True
        )(payload=payload, user_id=request.user.id)
    except Card.DoesNotExist:
        # 404 — never 403 — for the same enumeration-protection reason
        # as decks/cards: don't leak that the id exists but isn't yours.
        return Status(404, {"detail": "Card not found"})
    except IdempotencyKeyReused:
        return Status(409, {"detail": "idempotency_key_reused"})

    if outcome == "accepted":
        return Status(200, CardOut(**details))
    # outcome == "conflict": LWW rejected. Surface as 409 with the
    # server_state so the client can re-merge.
    return Status(
        409,
        {
            "detail": "stale_review",
            "server_state": details.get("server_state"),
        },
    )
