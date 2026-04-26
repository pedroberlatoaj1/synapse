"""Deck and Card models."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
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
    # Soft delete tombstone. NULL = alive; non-NULL = deleted at that
    # instant. CRUD endpoints filter `deleted_at__isnull=True`; the sync
    # pull endpoint deliberately includes tombstones so other devices
    # can replicate the deletion locally.
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            # Listing decks by owner is the hot read; avoid a full scan
            # on the user FK join.
            models.Index(fields=["user"], name="deck_user_idx"),
            # Composite cursor for /sync/changes: rows ordered by
            # (updated_at, id) within a user. Postgres can satisfy the
            # cursor predicate
            #   (updated_at > X) OR (updated_at = X AND id > Y)
            # via a single index range scan when the ordering matches.
            models.Index(
                fields=["user", "updated_at", "id"],
                name="deck_sync_cursor_idx",
            ),
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        related_name="cards",
    )
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
    # Soft delete tombstone — see the matching field on Deck for rationale.
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            # Daily session query: cards in deck X that are due today.
            models.Index(fields=["deck", "due_at"], name="card_deck_due_idx"),
            # Composite cursor for /sync/changes. Card.user is denormalized
            # from Deck.user so pull can scan a user's cards directly without
            # a join+sort over all of their decks.
            models.Index(
                fields=["user", "updated_at", "id"],
                name="card_sync_cursor_idx",
            ),
        ]
        constraints = [
            # Belt-and-suspenders: model-level choices reject bad values in
            # Python, but a stray INSERT from psql or a future raw migration
            # would slip past. CHECK enforces it at the DB.
            models.CheckConstraint(
                condition=Q(state__in=CardState.values),
                name="card_state_valid",
            ),
            models.CheckConstraint(
                condition=Q(interval_days__gte=0),
                name="card_interval_days_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(repetitions__gte=0),
                name="card_repetitions_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"Card({self.id})"

    def save(self, *args, **kwargs):
        if self.user_id is None and self.deck_id is not None:
            if getattr(self, "deck", None) is not None:
                self.user_id = self.deck.user_id
            else:
                self.user_id = Deck.objects.only("user_id").get(id=self.deck_id).user_id
        super().save(*args, **kwargs)
