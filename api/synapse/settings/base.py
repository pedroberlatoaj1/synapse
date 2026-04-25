"""Base settings shared across dev / test / prod."""
from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# api/synapse/settings/base.py -> repo root is parents[3]
BASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BASE_DIR.parent

# Load .env from the repo root if present (dev convenience).
load_dotenv(REPO_ROOT / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "ninja_extra",
    "ninja_jwt",
    # Local apps
    "apps.accounts",
    "apps.decks",
    "apps.reviews",
    "apps.sync",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "synapse.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "synapse.wsgi.application"
ASGI_APPLICATION = "synapse.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "DATABASE_URL",
            "postgres://synapse:synapse@localhost:5432/synapse",
        ),
        conn_max_age=60,
    ),
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- ninja-jwt ---
# Lifetimes are env-driven so prod can shorten them without a code change.
# Defaults match .env.example: 60-minute access, 7-day refresh.
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": _dt.timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_LIFETIME_MINUTES", "60")),
    ),
    "REFRESH_TOKEN_LIFETIME": _dt.timedelta(
        days=int(os.environ.get("JWT_REFRESH_LIFETIME_DAYS", "7")),
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
