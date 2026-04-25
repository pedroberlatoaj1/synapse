"""Deck and Card model invariants."""
from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from apps.decks.models import Card, CardState, Deck


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="owner@example.com",
        password="pw-12345!",
    )


@pytest.mark.django_db
def test_deck_pk_is_uuid_and_owned_by_user(user):
    deck = baker.make(Deck, user=user, name="Anatomy")
    assert isinstance(deck.pk, uuid.UUID)
    assert deck.user_id == user.id


@pytest.mark.django_db
def test_deck_tags_default_empty_list(user):
    deck = Deck.objects.create(user=user, name="Empty")
    assert deck.tags == []


@pytest.mark.django_db
def test_deck_tags_array_round_trip(user):
    deck = Deck.objects.create(
        user=user,
        name="Tagged",
        tags=["med", "histology", "yr2"],
    )
    deck.refresh_from_db()
    assert deck.tags == ["med", "histology", "yr2"]


@pytest.mark.django_db
def test_deck_user_index_registered():
    names = {idx.name for idx in Deck._meta.indexes}
    assert "deck_user_idx" in names


@pytest.mark.django_db
def test_card_defaults_match_sm2_initial_state(user):
    deck = baker.make(Deck, user=user)
    card = Card.objects.create(deck=deck, front="Q", back="A")
    assert isinstance(card.pk, uuid.UUID)
    assert card.ease_factor == 2.5
    assert card.interval_days == 0
    assert card.repetitions == 0
    assert card.state == CardState.NEW
    assert card.due_at is not None  # default=now


@pytest.mark.django_db
def test_card_deck_due_index_registered():
    names = {idx.name for idx in Card._meta.indexes}
    assert "card_deck_due_idx" in names
