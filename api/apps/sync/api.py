"""Sync router: pull and push halves of the offline sync protocol.

GET /sync/changes returns Deck and Card changes for the authenticated user,
including soft-delete tombstones. Pagination uses an opaque base64 cursor over
the total ordering ``(updated_at, entity_type, id)``. The timestamp is encoded
with microsecond precision so JSON serialization cannot round it and cause a
row to be replayed on the next page.

POST /sync (Bloco 11) ingests a batch of offline events from a single device.
Every event runs in its own short transaction so a slow row lock on entity X
never blocks event Y. Inside each transaction we:

1. Acquire ``pg_advisory_xact_lock(hashtextextended(user_id||entity_id))``.
   Two devices replaying offline events for the same entity now serialize at
   this point — without that lock, two simultaneous updates could each read
   the same baseline and write back inconsistent next-states.
2. Try ``INSERT INTO sync_syncevent ... ON CONFLICT (id) DO NOTHING`` to claim
   the event id. A retry of an already-applied event short-circuits as
   ``accepted`` without touching the entity again.
3. ``select_for_update`` the target Deck/Card scoped to ``user_id == request.user.id``.
   A row in another user's space is invisible — the predicate yields
   ``DoesNotExist`` and the event surfaces as a conflict, never a 403/404
   that would leak existence.
4. LWW: compare ``(incoming.client_ts, incoming.id)`` against
   ``(entity.last_client_ts, entity.last_event_id)``. The newer tuple wins.
   The event UUID is the deterministic tiebreaker for tied timestamps.
5. Apply the mutation and stamp ``last_client_ts``, ``last_event_id``, and
   ``updated_at = timezone.now()``.

For ``op="review"`` we LWW-check the card up front, then delegate to
``apps.reviews.api._apply_review_tx`` so the SM-2 math stays in one place.
That helper does its own ``INSERT ... ON CONFLICT`` on the same SyncEvent id,
so retries naturally collapse into the existing idempotency dance there.
"""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from datetime import UTC, datetime
from typing import Literal

from asgiref.sync import sync_to_async
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.utils import timezone
from ninja import Query, Router
from ninja.errors import HttpError
from ninja.responses import Status

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Card, Deck
from apps.reviews.api import IdempotencyKeyReused, _apply_review_tx
from apps.reviews.schemas import ReviewIn
from apps.sync.schemas import (
    PushConflict,
    PushIn,
    PushResponse,
    SyncEventItem,
    SyncPullResponse,
)

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


# === POST / (push) ========================================================

# Sentinels used in the LWW comparison when an entity has never been
# touched by a sync event before — that maps to (epoch, all-zeros UUID),
# both of which are strictly less than any real (client_ts, event_id),
# so a first-ever event always wins.
_LWW_NEVER_TS = datetime.min.replace(tzinfo=UTC)
_LWW_NEVER_ID = uuid.UUID(int=0)


def _serialize_deck(deck: Deck) -> dict:
    return {
        "id": str(deck.id),
        "name": deck.name,
        "description": deck.description,
        "is_public": deck.is_public,
        "updated_at": deck.updated_at.isoformat(),
        "deleted_at": deck.deleted_at.isoformat() if deck.deleted_at else None,
    }


def _serialize_card(card: Card) -> dict:
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


def _lww_loses(
    incoming_ts: datetime,
    incoming_id: uuid.UUID,
    entity_ts: datetime | None,
    entity_id: uuid.UUID | None,
) -> bool:
    """True if the incoming event should LOSE to the stored signature.

    Comparison is over the tuple (client_ts, event_id) — the older
    timestamp loses, and ties are broken by event UUID order so the
    decision is deterministic regardless of which device's request
    arrived at the server first.
    """
    baseline_ts = entity_ts or _LWW_NEVER_TS
    baseline_id = entity_id or _LWW_NEVER_ID
    return (incoming_ts, incoming_id) <= (baseline_ts, baseline_id)


def _take_advisory_lock(cursor, user_id: int, entity_id: uuid.UUID) -> None:
    """Serialize all events for ``(user, entity)`` within this transaction.

    The lock is auto-released when the transaction ends, so per-event
    transactions naturally bound the lock lifetime — no risk of a slow
    request holding the lock while we queue dozens more events.
    """
    cursor.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
        [f"{user_id}:{entity_id}"],
    )


def _claim_sync_event(
    cursor,
    *,
    event: SyncEventItem,
    user_id: int,
    device_id: str,
) -> bool:
    """Try to insert the SyncEvent row; return True if THIS call won.

    A False return means the row already existed — i.e. the event was
    already applied by an earlier request. The caller short-circuits
    that as ``accepted`` to keep retries idempotent.
    """
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
            str(event.id),
            user_id,
            device_id,
            event.entity_type,
            str(event.entity_id),
            event.op,
            json.dumps({"request": event.payload}),
            event.client_ts,
            "applied",
        ],
    )
    return cursor.fetchone() is not None


def _apply_create(
    *,
    event: SyncEventItem,
    user_id: int,
    now: datetime,
) -> tuple[Literal["accepted", "conflict"], dict | None]:
    """Insert a new Deck/Card with the LWW signature stamped on creation."""
    if event.entity_type == "deck":
        try:
            Deck.objects.create(
                id=event.entity_id,
                user_id=user_id,
                name=event.payload.get("name", ""),
                description=event.payload.get("description", ""),
                is_public=event.payload.get("is_public", False),
                last_client_ts=event.client_ts,
                last_event_id=event.id,
                updated_at=now,
            )
        except IntegrityError:
            # Another device already created an entity with this id; the
            # owner of that row is authoritative. We surface as a conflict
            # rather than overwriting blindly.
            return "conflict", {"reason": "entity_already_exists"}
        return "accepted", None

    # entity_type == "card"
    deck_id = event.payload.get("deck_id")
    if deck_id is None:
        return "conflict", {"reason": "missing_deck_id"}
    if not Deck.objects.filter(
        id=deck_id, user_id=user_id, deleted_at__isnull=True
    ).exists():
        return "conflict", {"reason": "deck_not_found"}
    try:
        Card.objects.create(
            id=event.entity_id,
            deck_id=deck_id,
            user_id=user_id,
            front=event.payload.get("front", ""),
            back=event.payload.get("back", ""),
            last_client_ts=event.client_ts,
            last_event_id=event.id,
            updated_at=now,
        )
    except IntegrityError:
        return "conflict", {"reason": "entity_already_exists"}
    return "accepted", None


def _apply_update_or_delete(
    *,
    event: SyncEventItem,
    user_id: int,
    now: datetime,
) -> tuple[Literal["accepted", "conflict"], dict | None]:
    """LWW-checked update/delete on an existing Deck or Card."""
    Model = Deck if event.entity_type == "deck" else Card
    try:
        entity = Model.objects.select_for_update().get(
            id=event.entity_id, user_id=user_id
        )
    except Model.DoesNotExist:
        # Foreign id, foreign user, or never created — same response in
        # all three cases so the user space stays unobservable.
        return "conflict", {"reason": "entity_not_found"}

    if _lww_loses(event.client_ts, event.id, entity.last_client_ts, entity.last_event_id):
        serialize = _serialize_deck if isinstance(entity, Deck) else _serialize_card
        return "conflict", {"reason": "stale_event", "server_state": serialize(entity)}

    update_fields = ["last_client_ts", "last_event_id", "updated_at"]
    if event.op == "delete":
        # Deletes don't read the payload — they just stamp the tombstone.
        # For Deck, cascade the soft delete to its still-alive cards so
        # the user's other devices see one consistent "everything in
        # this deck is gone" event.
        entity.deleted_at = now
        update_fields.append("deleted_at")
        if isinstance(entity, Deck):
            Card.objects.filter(
                deck_id=entity.id, user_id=user_id, deleted_at__isnull=True
            ).update(deleted_at=now, updated_at=now)
    else:
        # op == "update": apply only the writable fields the client sent,
        # ignoring extras so a malicious payload can't smuggle an
        # ease_factor injection past the SM-2 engine.
        if isinstance(entity, Deck):
            for field in ("name", "description", "is_public"):
                if field in event.payload:
                    setattr(entity, field, event.payload[field])
                    update_fields.append(field)
        else:
            for field in ("front", "back"):
                if field in event.payload:
                    setattr(entity, field, event.payload[field])
                    update_fields.append(field)

    entity.last_client_ts = event.client_ts
    entity.last_event_id = event.id
    entity.updated_at = now
    entity.save(update_fields=update_fields)
    return "accepted", None


def _apply_review_event(
    *,
    event: SyncEventItem,
    user_id: int,
    device_id: str,
) -> tuple[Literal["accepted", "conflict"], dict | None]:
    """LWW-check the card, then delegate to the existing review pipeline.

    The review path's own ``_apply_review_tx`` handles the SyncEvent
    INSERT (so we DON'T pre-claim it here for review events) and the
    SM-2 math; we just gatekeep stale events at the door.
    """
    rating = event.payload.get("rating")
    duration_ms = event.payload.get("duration_ms")
    if rating is None or duration_ms is None:
        return "conflict", {"reason": "invalid_review_payload"}

    with transaction.atomic():
        with connection.cursor() as cur:
            _take_advisory_lock(cur, user_id, event.entity_id)
        try:
            card = Card.objects.select_for_update().get(
                id=event.entity_id,
                user_id=user_id,
                deck__deleted_at__isnull=True,
                deleted_at__isnull=True,
            )
        except Card.DoesNotExist:
            return "conflict", {"reason": "card_not_found"}

        if _lww_loses(event.client_ts, event.id, card.last_client_ts, card.last_event_id):
            return "conflict", {
                "reason": "stale_event",
                "server_state": _serialize_card(card),
            }

    # Lock released before delegating. _apply_review_tx opens its own
    # transaction with its own lock + dedupe machinery; an incoming
    # event from a device replaying the same review now collapses into
    # idempotent retry semantics inside that helper.
    review_in = ReviewIn(
        card_id=event.entity_id,
        rating=rating,
        duration_ms=duration_ms,
        client_event_id=event.id,
        device_id=device_id,
        client_ts=event.client_ts,
    )
    try:
        _apply_review_tx(payload=review_in, user_id=user_id)
    except IdempotencyKeyReused:
        return "conflict", {"reason": "idempotency_key_reused"}
    except Card.DoesNotExist:
        return "conflict", {"reason": "card_not_found"}
    return "accepted", None


def _apply_event(
    *,
    event: SyncEventItem,
    user_id: int,
    device_id: str,
) -> tuple[Literal["accepted", "conflict"], dict | None]:
    """Process one event in its own short transaction.

    The per-event boundary is deliberate. A 500-event batch with one
    contended row should not deadlock the other 499 events behind it:
    each event takes its own advisory lock, holds it for the duration
    of one INSERT/UPDATE pair, and releases on commit.
    """
    if event.op == "review":
        return _apply_review_event(event=event, user_id=user_id, device_id=device_id)

    now = timezone.now()
    with transaction.atomic():
        with connection.cursor() as cur:
            _take_advisory_lock(cur, user_id, event.entity_id)
            event_was_new = _claim_sync_event(
                cur, event=event, user_id=user_id, device_id=device_id
            )
        if not event_was_new:
            # Already processed in a previous request; treat as accepted
            # so retries are visibly idempotent in the response shape.
            return "accepted", None

        if event.op == "create":
            return _apply_create(event=event, user_id=user_id, now=now)
        if event.op in ("update", "delete"):
            return _apply_update_or_delete(event=event, user_id=user_id, now=now)

    # Pydantic's Literal already prunes invalid ops at request parse
    # time, but defensive: surface anything else as a conflict.
    return "conflict", {"reason": "unsupported_op"}


@router.post("", response={200: PushResponse})
async def push(request, payload: PushIn):
    accepted: list[uuid.UUID] = []
    conflicts: list[PushConflict] = []
    user_id = request.user.id

    for event in payload.events:
        try:
            outcome, details = await sync_to_async(
                _apply_event, thread_sensitive=True
            )(event=event, user_id=user_id, device_id=payload.device_id)
        except Exception as exc:  # noqa: BLE001 — defense-in-depth boundary
            conflicts.append(
                PushConflict(
                    event_id=event.id,
                    reason=f"server_error:{type(exc).__name__}",
                )
            )
            continue

        if outcome == "accepted":
            accepted.append(event.id)
        else:
            conflicts.append(
                PushConflict(
                    event_id=event.id,
                    reason=(details or {}).get("reason", "unknown"),
                    server_state=(details or {}).get("server_state"),
                )
            )

    return Status(200, PushResponse(accepted=accepted, conflicts=conflicts))
