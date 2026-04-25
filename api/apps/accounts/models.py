"""User model — UUID PK, email is the unique identifier."""
from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone as dj_timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    timezone = models.CharField(max_length=64, default="UTC")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=dj_timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "auth_user"
        constraints = [
            # Defense-in-depth: even if something bypasses the manager and
            # writes a mixed-case email, the DB enforces uniqueness on LOWER(email).
            models.UniqueConstraint(Lower("email"), name="user_email_lower_uniq"),
        ]

    def __str__(self) -> str:
        return self.email
