"""Review log — historical record of every SM-2 evaluation."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone as dj_timezone


class ReviewRating(models.TextChoices):
    AGAIN = "again", "Again"
    HARD = "hard", "Hard"
    GOOD = "good", "Good"
    EASY = "easy", "Easy"


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    card = models.ForeignKey(
        "decks.Card",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.CharField(max_length=8, choices=ReviewRating.choices)

    # SM-2 transition snapshot
    prev_interval = models.IntegerField()
    new_interval = models.IntegerField()

    duration_ms = models.IntegerField()
    reviewed_at = models.DateTimeField(default=dj_timezone.now)

    class Meta:
        indexes = [
            # Heatmap and stats queries scan the user's reviews newest-first.
            models.Index(fields=["user", "-reviewed_at"], name="review_user_when_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__in=ReviewRating.values),
                name="review_rating_valid",
            ),
            models.CheckConstraint(
                condition=Q(duration_ms__gte=0),
                name="review_duration_ms_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"Review({self.id} {self.rating})"
