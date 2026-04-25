"""Project-local Bearer auth class — single import for protected routers."""
from __future__ import annotations

from asgiref.sync import sync_to_async
from ninja_jwt.authentication import JWTAuth


class AsyncJWTAuth(JWTAuth):
    """Async-friendly JWT Bearer auth.

    Bloco 5+ exposes async routers (Decks/Cards/Review). JWTAuth's user
    lookup is synchronous and would block the event loop, so we override
    the auth entrypoint to run the parent's logic in a thread.

    Single canonical class for protected endpoints — keeps the import
    site stable while we evolve auth side-effects (e.g. last-seen
    updates, audit logging) in one place.
    """

    async def __call__(self, request):  # type: ignore[override]
        return await sync_to_async(super().__call__, thread_sensitive=False)(request)
