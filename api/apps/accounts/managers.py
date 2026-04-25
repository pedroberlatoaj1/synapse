"""Custom user manager — email is the natural key, normalized lowercase."""
from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        # BaseUserManager only lowercases the domain part. We want the full
        # address lowercased so equality (and the LOWER(email) unique
        # constraint) behave the same in Python and in Postgres.
        email = super().normalize_email(email or "")
        return email.lower()

    def _create_user(self, email: str, password: str | None, **extra: Any):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: Any):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra: Any):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra)

    def get_by_natural_key(self, username: str):
        # Django's auth backend calls this during login. Stored emails are
        # lowercase; lowercase the lookup so "Bob@x.com" matches "bob@x.com".
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})
