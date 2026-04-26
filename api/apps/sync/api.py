"""Sync router: pull-side of the offline sync protocol.

GET /sync/changes returns Deck and Card changes for the authenticated user,
including soft-delete tombstones. Pagination uses an opaque base64 cursor over
the total ordering ``(updated_at, entity_type, id)``. The timestamp is encoded
with microsecond precision so JSON serialization cannot round it and cause a
row to be replayed on the next page.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from ninja import Query, Router
from ninja.errors import HttpError

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Card, Deck
from apps.sync.schemas import SyncPullResponse

router = Router(auth=AsyncJWTAuth(), tags=["Sync"])

_DECK_FIELDS = (
    "id",
    "name",
    "description",
    "is_public",
    "updated_at",
    "deleted_at",
)

_CARD_FIELDS = (
    "id",
    "deck_id",
    "front",
    "back",
    "state",
    "ease_factor",
    "interval_days",
    "repetitions",
    "due_at",
    "updated_at",
    "deleted_at",
)

_ENTITY_TYPES = frozenset({"card", "deck"})


def _encode_cursor(updated_at: datetime, entity_type: str, entity_id: uuid.UUID) -> str:
    raw = f"{updated_at.isoformat(timespec='microseconds')}|{entity_type}|{entity_id}"
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str | None) -> tuple[datetime, str, uuid.UUID] | None:
    if cursor is None:
        return None

    try:
        raw = base64.b64decode(cursor.encode("ascii"), validate=True).decode("utf-8")
        cursor_ts_raw, entity_type, entity_id_raw = raw.split("|", 2)
        if entity_type not in _ENTITY_TYPES:
            raise ValueError("unknown entity type")
        return datetime.fromisoformat(cursor_ts_raw), entity_type, uuid.UUID(entity_id_raw)
    except (binascii.Error, UnicodeError, ValueError) as exc:
        raise HttpError(400, "Invalid sync cursor") from exc


def _cursor_filter(
    cursor_state: tuple[datetime, str, uuid.UUID] | None,
    entity_type: str,
) -> Q:
    """Translate the opaque cursor into a per-entity range predicate."""
    if cursor_state is None:
        return Q()

    cursor_ts, cursor_entity_type, cursor_id = cursor_state
    after_timestamp = Q(updated_at__gt=cursor_ts)

    if entity_type > cursor_entity_type:
        return after_timestamp | Q(updated_at=cursor_ts)
    if entity_type == cursor_entity_type:
        return after_timestamp | (Q(updated_at=cursor_ts) & Q(id__gt=cursor_id))
    return after_timestamp


@router.get("/changes", response=SyncPullResponse)
async def changes(
    request,
    cursor: str | None = None,
    limit: int = Query(500, ge=1, le=2000),
):
    """Return the next page of Deck/Card changes for the authenticated user."""
    server_now = timezone.now()
    cursor_state = _decode_cursor(cursor)

    deck_qs = (
        Deck.objects.filter(user=request.user, updated_at__lte=server_now)
        .filter(_cursor_filter(cursor_state, "deck"))
        .order_by("updated_at", "id")
        .values(*_DECK_FIELDS)[: limit + 1]
    )
    card_qs = (
        Card.objects.filter(user=request.user, updated_at__lte=server_now)
        .filter(_cursor_filter(cursor_state, "card"))
        .order_by("updated_at", "id")
        .values(*_CARD_FIELDS)[: limit + 1]
    )

    decks_raw = [d async for d in deck_qs]
    cards_raw = [c async for c in card_qs]

    deck_has_more = len(decks_raw) > limit
    card_has_more = len(cards_raw) > limit
    decks_raw = decks_raw[:limit]
    cards_raw = cards_raw[:limit]

    combined: list[tuple[datetime, str, uuid.UUID, dict]] = []
    for deck in decks_raw:
        combined.append((deck["updated_at"], "deck", deck["id"], deck))
    for card in cards_raw:
        combined.append((card["updated_at"], "card", card["id"], card))
    combined.sort(key=lambda row: (row[0], row[1], row[2]))

    truncated = combined[limit:]
    page = combined[:limit]
    has_more = deck_has_more or card_has_more or bool(truncated)

    out_decks = [row[3] for row in page if row[1] == "deck"]
    out_cards = [row[3] for row in page if row[1] == "card"]
    if page:
        last = page[-1]
        next_cursor = _encode_cursor(last[0], last[1], last[2])
    else:
        next_cursor = None

    return {
        "server_now": server_now,
        "decks": out_decks,
        "cards": out_cards,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }
