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

from ninja import Schema


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
