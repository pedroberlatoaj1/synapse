"""Cards router — async CRUD scoped to the authenticated user.

Multi-tenant isolation works in two hops: Card -> Deck -> User. Every
query/update/delete joins through `deck__user=request.user`. A card that
belongs to someone else's deck returns 404 (NOT 403) for the same
enumeration-protection reason as decks.
"""
import uuid

from ninja import Router
from ninja.pagination import paginate
from ninja.responses import Status

from apps.accounts.auth import AsyncJWTAuth
from apps.decks.models import Card, Deck
from apps.decks.schemas import CardCreate, CardOut, CardUpdate

router = Router(auth=AsyncJWTAuth(), tags=["Cards"])


def _card_out(card: Card) -> CardOut:
    return CardOut(
        id=card.id,
        deck_id=card.deck_id,
        front=card.front,
        back=card.back,
        state=card.state,
        due_at=card.due_at,
    )


@router.post("", response={201: CardOut, 404: dict})
async def create_card(request, payload: CardCreate):
    # Ownership check via the deck — filtering by user blocks creating a
    # card inside someone else's deck. 404 (not 403) keeps deck-id space
    # opaque to attackers.
    if not await Deck.objects.filter(id=payload.deck_id, user=request.user).aexists():
        return Status(404, {"detail": "Deck not found"})

    card = await Card.objects.acreate(
        deck_id=payload.deck_id,
        front=payload.front,
        back=payload.back,
    )
    return Status(201, _card_out(card))


@router.get("", response=list[CardOut])
@paginate
async def list_cards(request, deck_id: uuid.UUID):
    # deck_id is required so the client always scopes to one deck. The
    # deck__user filter makes a foreign deck_id yield an empty page
    # rather than leaking that the deck exists.
    return (
        Card.objects.filter(deck_id=deck_id, deck__user=request.user)
        .order_by("-created_at")
        .values("id", "deck_id", "front", "back", "state", "due_at")
    )


@router.patch("/{card_id}", response={200: CardOut, 404: dict})
async def update_card(request, card_id: uuid.UUID, payload: CardUpdate):
    try:
        card = await Card.objects.select_related("deck").aget(
            id=card_id, deck__user=request.user
        )
    except Card.DoesNotExist:
        return Status(404, {"detail": "Card not found"})

    # exclude_unset drops fields the client didn't send; the None filter
    # drops explicit nulls so PATCH {"front": null} is a no-op instead of
    # crashing the NOT NULL TextField at the DB.
    update_data = {
        k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None
    }
    if not update_data:
        return Status(200, _card_out(card))

    for field, value in update_data.items():
        setattr(card, field, value)
    await card.asave(update_fields=[*update_data.keys(), "updated_at"])

    return Status(200, _card_out(card))


@router.delete("/{card_id}", response={204: None, 404: dict})
async def delete_card(request, card_id: uuid.UUID):
    deleted, _ = await Card.objects.filter(
        id=card_id, deck__user=request.user
    ).adelete()
    if deleted == 0:
        return Status(404, {"detail": "Card not found"})
    return Status(204, None)
