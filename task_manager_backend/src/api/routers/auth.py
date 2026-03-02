from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.errors import bad_request, unauthorized
from src.core.security import create_access_token, hash_password, verify_password
from src.dependencies.auth import get_current_user
from src.repositories.users import create_user, get_user_by_email
from src.schemas.auth import AuthSessionOut, LoginIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=AuthSessionOut,
    summary="Register a new user",
    description="Create a new user account and return an access token (JWT) plus user profile.",
    operation_id="auth_register",
)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> AuthSessionOut:
    """Register a new user and return a token + user.

    Args:
        payload: RegisterIn with email/password/name.
        db: Database session.

    Returns:
        AuthSessionOut containing token + user profile.
    """
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise bad_request("Email is already registered")

    try:
        user = create_user(
            db,
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            display_name=payload.name,
        )
    except IntegrityError:
        # In case of a race condition on unique email.
        raise bad_request("Email is already registered")

    token = create_access_token(user["id"])
    return AuthSessionOut(
        token=token,
        user=UserOut(id=user["id"], email=user["email"], display_name=user.get("display_name")),
    )


@router.post(
    "/login",
    response_model=AuthSessionOut,
    summary="Login",
    description="Verify email/password and return an access token (JWT) plus user profile.",
    operation_id="auth_login",
)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> AuthSessionOut:
    """Login and return a token + user."""
    user = get_user_by_email(db, str(payload.email))
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise unauthorized("Invalid email or password")

    token = create_access_token(user["id"])
    return AuthSessionOut(
        token=token,
        user=UserOut(id=user["id"], email=user["email"], display_name=user.get("display_name")),
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user",
    description="Return the profile of the current authenticated user.",
    operation_id="auth_me",
)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    """Return current user profile."""
    return UserOut(id=user["id"], email=user["email"], display_name=user.get("display_name"))


@router.post(
    "/logout",
    summary="Logout",
    description="Logout endpoint for client parity. Since JWT is stateless, this is a no-op.",
    operation_id="auth_logout",
)
def logout() -> dict:
    """Logout (no-op for stateless JWT)."""
    return {"ok": True}
