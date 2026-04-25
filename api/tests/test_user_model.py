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
