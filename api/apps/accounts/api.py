"""Auth endpoints — register, login, refresh, me.

Note: this module deliberately does NOT use `from __future__ import
annotations`. Pydantic v2 + ninja-extra's QueryParams wrapper can't
resolve string-form annotations like `"EmailStr"` from the wrapper's
namespace, so we keep type hints concrete here.
"""
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from ninja import Schema
from ninja.responses import Status
from ninja_extra import api_controller, http_get, http_post
from ninja_jwt.tokens import RefreshToken
from pydantic import EmailStr, Field

from apps.accounts.auth import AsyncJWTAuth


class RegisterIn(Schema):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginIn(Schema):
    email: EmailStr
    password: str = Field(..., max_length=128)


class TokenPair(Schema):
    access: str
    refresh: str


class RefreshIn(Schema):
    refresh: str = Field(..., min_length=1)


class MeOut(Schema):
    id: str
    email: EmailStr
    name: str


class ErrorOut(Schema):
    detail: str


def _token_pair_for(user) -> TokenPair:
    refresh = RefreshToken.for_user(user)
    return TokenPair(access=str(refresh.access_token), refresh=str(refresh))


def _display_name_for(user) -> str:
    get_full_name = getattr(user, "get_full_name", None)
    if callable(get_full_name):
        full_name = get_full_name()
        if full_name:
            return full_name
    return getattr(user, "name", "") or ""


@api_controller("/auth", tags=["Auth"])
class AuthController:
    """Auth surface for the Synapse API.

    Contract-level routes consumed by the Web and Mobile clients:

      POST /auth/register — sign up + token pair
      POST /auth/login    — authenticate + token pair
      POST /auth/refresh  — validate refresh + issue a fresh token pair
      GET  /auth/me       — authenticated user profile
    """

    @http_post(
        "/register",
        response={201: TokenPair, 400: ErrorOut},
        url_name="auth_register",
        auth=None,
    )
    def register(self, payload: RegisterIn):
        User = get_user_model()
        email = User.objects.normalize_email(payload.email)

        # Wrap in a savepoint: if the LOWER(email) constraint rejects a
        # case-conflicting duplicate, we want a clean 400 without
        # poisoning the surrounding request transaction.
        try:
            with transaction.atomic():
                user = User.objects.create_user(email=email, password=payload.password)
        except IntegrityError:
            return Status(400, ErrorOut(detail="Email already registered"))

        return Status(201, _token_pair_for(user))

    @http_post(
        "/login",
        response={200: TokenPair, 401: ErrorOut},
        url_name="auth_login",
        auth=None,
    )
    def login(self, payload: LoginIn):
        # authenticate goes through our custom UserManager.get_by_natural_key,
        # which does a case-insensitive lookup, so "Bob@x.com" matches the
        # stored "bob@x.com".
        user = authenticate(
            request=None,
            **{
                get_user_model().USERNAME_FIELD: payload.email,
                "password": payload.password,
            },
        )
        if user is None or not user.is_active:
            return Status(401, ErrorOut(detail="Invalid credentials"))
        return Status(200, _token_pair_for(user))

    @http_post(
        "/refresh",
        response={200: TokenPair, 401: ErrorOut},
        url_name="auth_refresh",
        auth=None,
    )
    def refresh(self, payload: RefreshIn):
        User = get_user_model()

        try:
            refresh = RefreshToken(payload.refresh)
            user_id = refresh.payload.get("user_id")
            if user_id is None:
                return Status(401, ErrorOut(detail="Invalid refresh token"))
            user = User.objects.get(id=user_id, is_active=True)
        except Exception:
            return Status(401, ErrorOut(detail="Invalid refresh token"))

        return Status(200, _token_pair_for(user))

    @http_get(
        "/me",
        response={200: MeOut},
        url_name="auth_me",
        auth=AsyncJWTAuth(),
    )
    async def me(self, request):
        user = request.user
        return MeOut(
            id=str(user.id),
            email=user.email,
            name=_display_name_for(user),
        )
