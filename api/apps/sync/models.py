"""Offline sync event log.

`SyncEvent.id` is generated CLIENT-SIDE (UUID v4/v7) and acts as the
idempotency key. The server inserts with `ON CONFLICT (id) DO NOTHING`
and reuses the same id as the Temporal `workflow_id` (`sync-event-{id}`),
so HTTP retries never fan out into duplicate workflows. See
docs/TECH_SPECS.md §4.1.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q


class SyncOp(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    REVIEW = "review", "Review"


class SyncStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPLIED = "applied", "Applied"
    CONFLICT = "conflict", "Conflict"


class SyncEvent(models.Model):
    # No `default=` — the client MUST supply the UUID. This is what makes
    # the server's INSERT ... ON CONFLICT (id) DO NOTHING idempotent.
    id = models.UUIDField(primary_key=True, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sync_events",
    )
    device_id = models.CharField(max_length=128)
    entity_type = models.CharField(max_length=32)
    entity_id = models.UUIDField()
    op = models.CharField(max_length=16, choices=SyncOp.choices)
    payload = models.JSONField()

    client_ts = models.DateTimeField()
    server_ts = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=16,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
    )

    class Meta:
        indexes = [
            # Per-device reconciliation in chronological order.
            models.Index(
                fields=["user", "device_id", "server_ts"],
                name="syncevent_user_device_idx",
            ),
            # Replaces the simple (user, status) index — lets the worker
            # poll the pending/conflict queue for a user in time order.
            models.Index(
                fields=["user", "status", "server_ts"],
                name="syncevent_user_status_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(op__in=SyncOp.values),
                name="syncevent_op_valid",
            ),
            models.CheckConstraint(
                condition=Q(status__in=SyncStatus.values),
                name="syncevent_status_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"SyncEvent({self.id} {self.op} {self.status})"
