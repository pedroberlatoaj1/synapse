"""Wire-format schemas for the /decks and /cards routers."""
import uuid
from datetime import datetime

from ninja import Schema
from pydantic import Field


class DeckCreate(Schema):
    name: str = Field(..., min_length=1, max_length=200)


class DeckUpdate(Schema):
    name: str = Field(..., min_length=1, max_length=200)


class DeckOut(Schema):
    id: uuid.UUID
    name: str


class CardCreate(Schema):
    deck_id: uuid.UUID
    front: str = Field(..., min_length=1, max_length=10000)
    back: str = Field(..., min_length=1, max_length=10000)


class CardUpdate(Schema):
    # Optional => partial PATCH. None means "leave unchanged". Handler
    # uses model_dump(exclude_unset=True) and filters Nones, so an explicit
    # null in the body is a no-op rather than a NOT NULL violation at the DB.
    front: str | None = Field(None, min_length=1, max_length=10000)
    back: str | None = Field(None, min_length=1, max_length=10000)


class CardOut(Schema):
    id: uuid.UUID
    deck_id: uuid.UUID
    front: str
    back: str
    state: str
    due_at: datetime
