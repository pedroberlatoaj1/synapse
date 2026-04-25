"""Production settings."""
import os

from .base import *  # noqa: F401,F403


def _env_bool(key: str, default: bool) -> bool:
    return os.environ.get(key, str(default)).lower() in {"1", "true", "yes"}


DEBUG = False

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]

# --- HTTPS hardening (env-driven, secure defaults) ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Force HTTPS on every request. Override to False only behind a TLS-terminating
# proxy that you trust to never serve plain HTTP, or for short ops escapes.
SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", True)

# HSTS: 1 year by default. Drop to 0 (disabled) only for incident response or
# if you need to back out of HTTPS — and remember preload submissions are sticky.
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    SECURE_HSTS_SECONDS > 0,
)
SECURE_HSTS_PRELOAD = _env_bool(
    "DJANGO_SECURE_HSTS_PRELOAD",
    SECURE_HSTS_SECONDS > 0,
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
