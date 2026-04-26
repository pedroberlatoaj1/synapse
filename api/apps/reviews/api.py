"""Reviews router — async queue + transactional review submission.

The two endpoints have very different concurrency profiles:

* ``GET /reviews/queue`` is a read-only point-in-time snapshot of due
  cards. Single SELECT, no lock, no transaction — runs natively async.

* ``POST /reviews`` mutates two tables (Card update + Review insert)
  and must be atomic. Django 5.2's ``transaction.atomic`` is still a
  sync context manager bound to the current thread's DB connection,
  so we cannot open it from inside ``async def`` without risking the
  block running on a thread that doesn't own the connection.
  The fix: pack the whole transactional sequence into a sync helper
  (`_apply_review_tx`) and dispatch it via ``sync_to_async(...,
  thread_sensitive=True)`` — that pins the work to the request's
  thread, keeps the atomic block coherent, and makes the lock and
  the rows it covers move together.

Why ``select_for_update`` inside the atomic block: two devices of the
same user replaying offline reviews can submit ratings for the same
card almost simultaneously. Without a row lock, both reads see the
same `state` and write back conflicting next-states (last-write-wins
on a stale read). FOR UPDATE serializes them at the Postgres level
so each rating is applied to the freshest state.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone
from ninja import Query, Router
from ninja.responses import Status

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Card
from apps.decks.schemas import CardOut
from apps.reviews.models import Review
from apps.reviews.schemas import ReviewIn
from apps.reviews.sm2 import calculate_next_state

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
            deck__user=request.user,
            due_at__lte=now,
        )
        .order_by("due_at")
        .values("id", "deck_id", "front", "back", "state", "due_at")[:limit]
    )
    return [card async for card in qs]


# --- POST / (submit a review) ---------------------------------------------

def _apply_review_tx(
    *,
    card_id: uuid.UUID,
    user_id: int,
    rating: str,
    duration_ms: int,
) -> dict:
    """Sync transactional core of POST /reviews.

    Runs entirely on a single thread under one DB connection so the
    ``transaction.atomic`` block, the ``SELECT ... FOR UPDATE`` lock,
    and the subsequent writes all share the same session. Raises
    ``Card.DoesNotExist`` if the card is missing or owned by another
    user — the caller maps that to 404.
    """
    with transaction.atomic():
        # Lock the row before reading the SM-2 fields. Two concurrent
        # reviews on the same card now serialize at this point.
        card = Card.objects.select_for_update().get(
            id=card_id, deck__user_id=user_id
        )

        prev_interval = card.interval_days
        next_state = calculate_next_state(
            state=card.state,
            ease_factor=card.ease_factor,
            interval_days=card.interval_days,
            repetitions=card.repetitions,
            rating=rating,
        )
        new_due_at = timezone.now() + timedelta(days=next_state["interval_days"])

        card.state = next_state["state"]
        card.ease_factor = next_state["ease_factor"]
        card.interval_days = next_state["interval_days"]
        card.repetitions = next_state["repetitions"]
        card.due_at = new_due_at
        card.save(
            update_fields=[
                "state",
                "ease_factor",
                "interval_days",
                "repetitions",
                "due_at",
                "updated_at",
            ]
        )

        # Snapshot the transition for the audit/heatmap query later.
        Review.objects.create(
            card=card,
            user_id=user_id,
            rating=rating,
            prev_interval=prev_interval,
            new_interval=next_state["interval_days"],
            duration_ms=duration_ms,
        )

        # Return a plain dict so the value crosses the sync_to_async
        # boundary cheaply — the async handler wraps it in CardOut.
        return {
            "id": card.id,
            "deck_id": card.deck_id,
            "front": card.front,
            "back": card.back,
            "state": card.state,
            "due_at": card.due_at,
        }


@router.post("", response={200: CardOut, 404: dict})
async def submit_review(request, payload: ReviewIn):
    try:
        data = await sync_to_async(_apply_review_tx, thread_sensitive=True)(
            card_id=payload.card_id,
            user_id=request.user.id,
            rating=payload.rating,
            duration_ms=payload.duration_ms,
        )
    except Card.DoesNotExist:
        # 404 — never 403 — for the same enumeration-protection reason
        # as decks/cards: don't leak that the id exists but isn't yours.
        return Status(404, {"detail": "Card not found"})

    return Status(200, CardOut(**data))
