"""Project-local Bearer JWT auth.

Single import path for protected routers. We use ninja-jwt's native
AsyncJWTAuth (which inherits from AsyncHttpBearer and already wraps the
sync DB lookups with sync_to_async) instead of rolling our own wrapper —
the native class handles the validate-token + load-user split correctly
with two separate thread-pool hops, while a naive __call__ wrapper would
serialize them.

Re-exported here so auth endpoints and protected routers in apps/decks,
apps/reviews, and apps/sync keep importing from a stable project module.
"""
from ninja_jwt.authentication import AsyncJWTAuth

__all__ = ["AsyncJWTAuth"]
