from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    """User profile returned to the frontend."""

    id: str = Field(..., description="User id (UUID).")
    email: EmailStr = Field(..., description="User email.")
    display_name: str | None = Field(None, description="Optional display name.")


class AuthSessionOut(BaseModel):
    """Auth session returned by register/login endpoints."""

    token: str = Field(..., description="Bearer token (JWT).")
    user: UserOut = Field(..., description="Current user profile.")


class RegisterIn(BaseModel):
    """Registration payload."""

    email: EmailStr = Field(..., description="Email address.")
    password: str = Field(..., description="Password (min 8 chars).", min_length=8)
    name: str | None = Field(None, description="Optional display name.")


class LoginIn(BaseModel):
    """Login payload."""

    email: EmailStr = Field(..., description="Email address.")
    password: str = Field(..., description="Password.", min_length=1)
