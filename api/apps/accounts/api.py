"""Auth endpoints — register, login, refresh.

Note: this module deliberately does NOT use `from __future__ import
annotations`. Pydantic v2 + ninja-extra's QueryParams wrapper can't
resolve string-form annotations like `"EmailStr"` from the wrapper's
namespace, so we keep type hints concrete here.
"""
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from ninja import Schema
from ninja.responses import Status
from ninja_extra import api_controller, http_post
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_jwt.tokens import RefreshToken
from pydantic import EmailStr, Field


class RegisterIn(Schema):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginIn(Schema):
    email: EmailStr
    password: str = Field(..., max_length=128)


class TokenPair(Schema):
    access: str
    refresh: str


class ErrorOut(Schema):
    detail: str


def _token_pair_for(user) -> TokenPair:
    refresh = RefreshToken.for_user(user)
    return TokenPair(access=str(refresh.access_token), refresh=str(refresh))


@api_controller("/auth", tags=["Auth"])
class AuthController(NinjaJWTDefaultController):
    """Auth surface for the Synapse API.

    Inheriting NinjaJWTDefaultController gives us /auth/pair, /auth/refresh,
    and /auth/verify out of the box. We add the contract-level routes:

      POST /auth/register — sign up + token pair
      POST /auth/login    — authenticate + token pair (the spec name;
                            /pair stays as a side-effect alias)

    /auth/refresh comes inherited from the parent and matches the spec.
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
