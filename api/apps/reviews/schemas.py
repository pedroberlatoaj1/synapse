"""Wire-format schemas for the /reviews router."""
import uuid
from datetime import datetime
from typing import Literal

from ninja import Schema
from pydantic import Field


class ReviewIn(Schema):
    card_id: uuid.UUID
    # Literal => Pydantic rejects anything outside the SM-2 rating set
    # at request-validation time, so the engine never receives garbage
    # and the DB-level CHECK constraint stays a defense-in-depth layer.
    rating: Literal["again", "hard", "good", "easy"]
    duration_ms: int = Field(..., ge=0)

    # Idempotency envelope (Bloco 9). The client supplies these on every
    # POST. `client_event_id` is the dedupe key — the server stores it as
    # the PK of a SyncEvent row and refuses to re-apply on retries.
    # `device_id` and `client_ts` go into the request snapshot we compare
    # against on retry, so the same id reused with a different rating or
    # timestamp surfaces as a 409 instead of silently winning.
    client_event_id: uuid.UUID
    device_id: str = Field(..., min_length=1, max_length=128)
    client_ts: datetime
