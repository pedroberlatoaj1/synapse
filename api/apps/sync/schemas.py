"""Wire-format schemas for the /sync router.

Sync schemas intentionally diverge from the CRUD schemas (DeckOut /
CardOut) on two fields:

* ``updated_at`` — required for the client to advance its watermark.
* ``deleted_at`` — required for the client to apply tombstones locally.

Keeping them separate means the public CRUD payload stays minimal
(no leak of when something was last touched, no tombstone surface)
while the sync surface carries everything a replica needs.
"""
import uuid
from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import Field


class DeckSync(Schema):
    id: uuid.UUID
    name: str
    description: str
    is_public: bool
    updated_at: datetime
    deleted_at: datetime | None


class CardSync(Schema):
    id: uuid.UUID
    deck_id: uuid.UUID
    front: str
    back: str
    state: str
    ease_factor: float
    interval_days: int
    repetitions: int
    due_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class SyncPullResponse(Schema):
    server_now: datetime
    decks: list[DeckSync]
    cards: list[CardSync]
    has_more: bool
    next_cursor: str | None


# --- Push (Bloco 11) -------------------------------------------------------


class SyncEventItem(Schema):
    """One entry in a sync push batch.

    The client supplies ``id`` (UUID) — this becomes the SyncEvent PK
    and the idempotency key for this exact event. ``client_ts`` is the
    client's local clock at the moment the user took the action; it is
    the LWW comparison key (server clock is never used for ordering
    offline edits).
    """
    id: uuid.UUID
    op: Literal["create", "update", "delete", "review"]
    entity_type: Literal["deck", "card"]
    entity_id: uuid.UUID
    client_ts: datetime
    payload: dict


class PushIn(Schema):
    device_id: str = Field(..., min_length=1, max_length=128)
    events: list[SyncEventItem] = Field(..., max_length=500)


class PushConflict(Schema):
    """One rejected event with the reason and (when relevant) the
    server's current view of the entity, so the client can re-merge."""
    event_id: uuid.UUID
    reason: str
    server_state: dict | None = None


class PushResponse(Schema):
    accepted: list[uuid.UUID]
    conflicts: list[PushConflict]
