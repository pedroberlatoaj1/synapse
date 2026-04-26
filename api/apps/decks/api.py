"""Decks router — async CRUD scoped to the authenticated user.

Multi-tenant isolation: every query/update/delete filters by the
authenticated user. Looking up a deck owned by someone else returns 404
(NOT 403) on purpose — leaking 'this resource exists but is not yours'
would let an attacker enumerate IDs.

Soft delete (Bloco 10): DELETE flips ``deleted_at`` to NOW() instead of
removing the row. Every read filters ``deleted_at__isnull=True`` so the
client never sees tombstones via this endpoint — those go through
``GET /sync/changes`` so other devices can replicate the deletion.
"""
import uuid

from django.utils import timezone
from ninja import Router
from ninja.pagination import paginate
from ninja.responses import Status

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Card, Deck
from apps.decks.schemas import DeckCreate, DeckOut, DeckUpdate

router = Router(auth=AsyncJWTAuth(), tags=["Decks"])


@router.post("", response={201: DeckOut})
async def create_deck(request, payload: DeckCreate):
    deck = await Deck.objects.acreate(user=request.user, name=payload.name)
    return Status(201, DeckOut(id=deck.id, name=deck.name))


@router.get("", response=list[DeckOut])
@paginate
async def list_decks(request):
    return (
        Deck.objects.filter(user=request.user, deleted_at__isnull=True)
        .order_by("-created_at")
        .values("id", "name")
    )


@router.patch("/{deck_id}", response={200: DeckOut, 404: dict})
async def update_deck(request, deck_id: uuid.UUID, payload: DeckUpdate):
    # Filter by user AND deleted_at: a soft-deleted deck is invisible
    # to PATCH so an attempt to "undelete" via this endpoint fails 404.
    try:
        deck = await Deck.objects.aget(
            id=deck_id, user=request.user, deleted_at__isnull=True
        )
    except Deck.DoesNotExist:
        return Status(404, {"detail": "Deck not found"})

    deck.name = payload.name
    await deck.asave(update_fields=["name", "updated_at"])
    return Status(200, DeckOut(id=deck.id, name=deck.name))


@router.delete("/{deck_id}", response={204: None, 404: dict})
async def delete_deck(request, deck_id: uuid.UUID):
    # Soft delete: stamp deleted_at instead of dropping the row, so
    # other devices learn about the deletion via /sync/changes. The
    # `deleted_at__isnull=True` filter makes a second DELETE on an
    # already-deleted deck return 404 (idempotent shape stays intact).
    now = timezone.now()
    updated = await Deck.objects.filter(
        id=deck_id, user=request.user, deleted_at__isnull=True
    ).aupdate(deleted_at=now, updated_at=now)
    if updated == 0:
        return Status(404, {"detail": "Deck not found"})
    await Card.objects.filter(
        deck_id=deck_id,
        user=request.user,
        deleted_at__isnull=True,
    ).aupdate(deleted_at=now, updated_at=now)
    return Status(204, None)
