"""Wire-format schemas for the /reviews router."""
import uuid
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
