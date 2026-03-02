from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.errors import unauthorized
from src.core.security import decode_access_token
from src.repositories.users import get_user_by_id

_security = HTTPBearer(auto_error=False)


# PUBLIC_INTERFACE
def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_security),
    db: Session = Depends(get_db),
) -> dict:
    """FastAPI dependency that returns the authenticated user profile dict."""
    if creds is None or not creds.credentials:
        raise unauthorized("Missing bearer token")

    token = creds.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise unauthorized("Invalid or expired token")

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise unauthorized("Invalid token subject")

    user = get_user_by_id(db, sub)
    if not user:
        raise unauthorized("User no longer exists")

    return user
