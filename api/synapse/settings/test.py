"""Test settings.

Tests run against the same Postgres engine as prod: ArrayField, JSONField,
advisory locks (Bloco 4), and DESC indexes are all Postgres-specific, and a
sqlite-only test rig would silently diverge from real schema.

First run creates `test_synapse`; subsequent runs reuse it (--reuse-db in
pyproject). Requires `make up` (compose stack) to be running.
"""
import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "TEST_DATABASE_URL",
            "postgres://synapse:synapse@localhost:5432/synapse",
        ),
        conn_max_age=0,
    ),
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
