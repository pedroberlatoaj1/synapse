"""Deck and Card models."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone as dj_timezone


class Deck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="decks",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    tags = ArrayField(
        models.CharField(max_length=64),
        default=list,
        blank=True,
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Listing decks by owner is the hot read; avoid a full scan
            # on the user FK join.
            models.Index(fields=["user"], name="deck_user_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class CardState(models.TextChoices):
    NEW = "new", "New"
    LEARNING = "learning", "Learning"
    REVIEW = "review", "Review"
    LAPSED = "lapsed", "Lapsed"


class Card(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards")
    front = models.TextField()
    back = models.TextField()

    # SM-2 state
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.IntegerField(default=0)
    repetitions = models.IntegerField(default=0)
    due_at = models.DateTimeField(default=dj_timezone.now)
    state = models.CharField(
        max_length=16,
        choices=CardState.choices,
        default=CardState.NEW,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Daily session query: cards in deck X that are due today.
            models.Index(fields=["deck", "due_at"], name="card_deck_due_idx"),
        ]

    def __str__(self) -> str:
        return f"Card({self.id})"
