"""Last-Writer-Wins primitives shared by /reviews and /sync.

Lives in its own module so both ``apps.reviews.api`` and
``apps.sync.api`` can import the same comparison without forming an
import cycle (sync.api imports from reviews.api for the SM-2 helpers,
so the LWW helpers can't live in either of those two files).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

# Sentinels used in the LWW comparison when an entity has never been
# touched by a sync event before. (epoch, all-zeros UUID) is strictly
# less than any real (client_ts, event_id) pair, so a first-ever event
# always wins against a never-touched baseline.
_LWW_NEVER_TS = datetime.min.replace(tzinfo=UTC)
_LWW_NEVER_ID = uuid.UUID(int=0)


def lww_loses(
    incoming_ts: datetime,
    incoming_id: uuid.UUID,
    entity_ts: datetime | None,
    entity_id: uuid.UUID | None,
) -> bool:
    """Return True if the incoming (ts, event_id) tuple should LOSE
    against the entity's last stamped (ts, event_id).

    Comparison is over the tuple itself: older client_ts loses; ties on
    timestamp are broken by event UUID order. Equality (same ts, same
    id) also loses — that case never legitimately reaches LWW because
    the SyncEvent dedupe table catches identical event ids first, so
    treating "equal" as a loss simply hardens the predicate against
    spoofed retries.
    """
    baseline_ts = entity_ts or _LWW_NEVER_TS
    baseline_id = entity_id or _LWW_NEVER_ID
    return (incoming_ts, incoming_id) <= (baseline_ts, baseline_id)


def serialize_card_state(card) -> dict:
    """JSON-friendly snapshot of a Card for the conflict ``server_state``.

    Used in the LWW conflict response so the client can re-merge against
    the server's authoritative view.
    """
    return {
        "id": str(card.id),
        "deck_id": str(card.deck_id),
        "front": card.front,
        "back": card.back,
        "state": card.state,
        "ease_factor": card.ease_factor,
        "interval_days": card.interval_days,
        "repetitions": card.repetitions,
        "due_at": card.due_at.isoformat(),
        "updated_at": card.updated_at.isoformat(),
        "deleted_at": card.deleted_at.isoformat() if card.deleted_at else None,
    }


def serialize_deck_state(deck) -> dict:
    return {
        "id": str(deck.id),
        "name": deck.name,
        "description": deck.description,
        "is_public": deck.is_public,
        "updated_at": deck.updated_at.isoformat(),
        "deleted_at": deck.deleted_at.isoformat() if deck.deleted_at else None,
    }
