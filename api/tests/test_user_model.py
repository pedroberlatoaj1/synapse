"""Custom user model invariants."""
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError


@pytest.mark.django_db
def test_user_pk_is_uuid():
    User = get_user_model()
    user = User.objects.create_user(email="alice@example.com", password="pw-12345!")
    assert isinstance(user.pk, uuid.UUID)


@pytest.mark.django_db
def test_email_is_unique():
    User = get_user_model()
    User.objects.create_user(email="bob@example.com", password="pw-12345!")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="bob@example.com", password="other-pw!")


@pytest.mark.django_db
def test_email_is_username_field():
    User = get_user_model()
    assert User.USERNAME_FIELD == "email"
    assert User.REQUIRED_FIELDS == []


@pytest.mark.django_db
def test_create_superuser_flags():
    User = get_user_model()
    admin = User.objects.create_superuser(email="root@example.com", password="pw-12345!")
    assert admin.is_staff is True
    assert admin.is_superuser is True


@pytest.mark.django_db
def test_email_is_normalized_to_lowercase():
    User = get_user_model()
    user = User.objects.create_user(email="Mixed.Case@Example.COM", password="pw-12345!")
    assert user.email == "mixed.case@example.com"


@pytest.mark.django_db(transaction=True)
def test_email_uniqueness_is_case_insensitive_at_db_level():
    """Bypass the manager and write a mixed-case email directly.

    The manager lowercases inputs, which masks whether the *database* is
    actually rejecting case-conflicting emails. This test exercises the
    UniqueConstraint(Lower('email')) — the only line of defence if a
    future raw SQL migration, admin shortcut, or bulk import skips the
    manager.
    """
    User = get_user_model()
    User.objects.create_user(email="dup@example.com", password="pw-12345!")
    raw = User(email="DUP@EXAMPLE.COM")
    raw.set_password("other-pw!")
    with pytest.raises(IntegrityError):
        raw.save()


@pytest.mark.django_db
def test_get_by_natural_key_is_case_insensitive():
    User = get_user_model()
    User.objects.create_user(email="alice@example.com", password="pw-12345!")
    found = User.objects.get_by_natural_key("Alice@Example.COM")
    assert found.email == "alice@example.com"
