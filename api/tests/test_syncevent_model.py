"""SyncEvent model invariants — id is the idempotency contract."""
from __future__ import annotations

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.sync.models import SyncEvent, SyncOp, SyncStatus


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="device@example.com",
        password="pw-12345!",
    )


def _make_event(user, **overrides):
    payload = {
        "id": uuid.uuid4(),
        "user": user,
        "device_id": "device-abc",
        "entity_type": "card",
        "entity_id": uuid.uuid4(),
        "op": SyncOp.CREATE,
        "payload": {"front": "Q", "back": "A"},
        "client_ts": timezone.now(),
    }
    payload.update(overrides)
    return SyncEvent.objects.create(**payload)


@pytest.mark.django_db
def test_id_is_client_supplied_and_persisted(user):
    client_id = uuid.uuid4()
    event = _make_event(user, id=client_id)
    assert event.pk == client_id


@pytest.mark.django_db
def test_status_defaults_to_pending(user):
    event = _make_event(user)
    assert event.status == SyncStatus.PENDING


@pytest.mark.django_db
def test_op_choices_match_spec():
    assert {c.value for c in SyncOp} == {"create", "update", "delete", "review"}


@pytest.mark.django_db
def test_status_choices_match_spec():
    assert {c.value for c in SyncStatus} == {"pending", "applied", "conflict"}


@pytest.mark.django_db
def test_duplicate_id_is_rejected(user):
    """The PK uniqueness is what enables INSERT ... ON CONFLICT (id) DO NOTHING."""
    same_id = uuid.uuid4()
    _make_event(user, id=same_id)
    with pytest.raises(IntegrityError):
        _make_event(user, id=same_id)


@pytest.mark.django_db
def test_payload_is_jsonfield_round_trip(user):
    event = _make_event(user, payload={"front": "Q", "tags": ["med"], "n": 3})
    event.refresh_from_db()
    assert event.payload == {"front": "Q", "tags": ["med"], "n": 3}


@pytest.mark.django_db
def test_required_indexes_registered():
    names = {idx.name for idx in SyncEvent._meta.indexes}
    assert {"syncevent_user_device_idx", "syncevent_user_status_idx"} <= names


@pytest.mark.django_db(transaction=True)
def test_save_without_id_raises_integrity_error(user):
    """Without `default=`, the PK has no value when the client forgets it.

    This guards the idempotency contract: callers MUST supply the UUID
    so the server can do INSERT ... ON CONFLICT (id) DO NOTHING and
    reuse it as the Temporal workflow_id (TECH_SPECS §4.1).
    """
    event = SyncEvent(
        # id intentionally omitted
        user=user,
        device_id="device-abc",
        entity_type="card",
        entity_id=uuid.uuid4(),
        op=SyncOp.CREATE,
        payload={"front": "Q"},
        client_ts=timezone.now(),
    )
    with pytest.raises(IntegrityError):
        event.save()
