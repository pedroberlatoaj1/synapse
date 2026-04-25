"""Decks router — async CRUD scoped to the authenticated user.

Multi-tenant isolation: every query/update/delete filters by the
authenticated user. Looking up a deck owned by someone else returns 404
(NOT 403) on purpose — leaking 'this resource exists but is not yours'
would let an attacker enumerate IDs.
"""
import uuid

from ninja import Router
from ninja.pagination import paginate
from ninja.responses import Status

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Deck
from apps.decks.schemas import DeckCreate, DeckOut, DeckUpdate

router = Router(auth=AsyncJWTAuth(), tags=["Decks"])


@router.post("", response={201: DeckOut})
async def create_deck(request, payload: DeckCreate):
    deck = await Deck.objects.acreate(user=request.user, name=payload.name)
    return Status(201, DeckOut(id=deck.id, name=deck.name))


@router.get("", response=list[DeckOut])
@paginate
async def list_decks(request):
    return Deck.objects.filter(user=request.user).order_by("-created_at").values("id", "name")


@router.patch("/{deck_id}", response={200: DeckOut, 404: dict})
async def update_deck(request, deck_id: uuid.UUID, payload: DeckUpdate):
    # Filter by user in the lookup itself: if the deck exists but belongs
    # to someone else, this raises DoesNotExist exactly like a missing id.
    try:
        deck = await Deck.objects.aget(id=deck_id, user=request.user)
    except Deck.DoesNotExist:
        return Status(404, {"detail": "Deck not found"})

    deck.name = payload.name
    await deck.asave(update_fields=["name", "updated_at"])
    return Status(200, DeckOut(id=deck.id, name=deck.name))


@router.delete("/{deck_id}", response={204: None, 404: dict})
async def delete_deck(request, deck_id: uuid.UUID):
    deleted, _ = await Deck.objects.filter(id=deck_id, user=request.user).adelete()
    if deleted == 0:
        return Status(404, {"detail": "Deck not found"})
    return Status(204, None)
