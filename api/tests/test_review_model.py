"""Review model invariants."""
from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from apps.decks.models import Card, Deck
from apps.reviews.models import Review, ReviewRating


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="learner@example.com",
        password="pw-12345!",
    )


@pytest.fixture
def card(user):
    deck = baker.make(Deck, user=user)
    return baker.make(Card, deck=deck)


@pytest.mark.django_db
def test_review_pk_is_uuid(user, card):
    review = Review.objects.create(
        card=card,
        user=user,
        rating=ReviewRating.GOOD,
        prev_interval=0,
        new_interval=1,
        duration_ms=1500,
    )
    assert isinstance(review.pk, uuid.UUID)


@pytest.mark.django_db
def test_review_rating_choices_cover_sm2_quartile():
    assert {c.value for c in ReviewRating} == {"again", "hard", "good", "easy"}


@pytest.mark.django_db
def test_review_user_when_index_registered():
    names = {idx.name for idx in Review._meta.indexes}
    assert "review_user_when_idx" in names


@pytest.mark.django_db
def test_review_index_orders_reviewed_at_desc():
    idx = next(i for i in Review._meta.indexes if i.name == "review_user_when_idx")
    # Newest-first scan for heatmap/stats — confirm the DESC marker.
    assert idx.fields == ["user", "-reviewed_at"]
