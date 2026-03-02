from __future__ import annotations

from fastapi import HTTPException, status


# PUBLIC_INTERFACE
def bad_request(message: str) -> HTTPException:
    """Create a 400 HTTPException with a consistent detail message."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


# PUBLIC_INTERFACE
def unauthorized(message: str = "Not authenticated") -> HTTPException:
    """Create a 401 HTTPException with a consistent detail message."""
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


# PUBLIC_INTERFACE
def forbidden(message: str = "Forbidden") -> HTTPException:
    """Create a 403 HTTPException with a consistent detail message."""
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


# PUBLIC_INTERFACE
def not_found(message: str = "Not found") -> HTTPException:
    """Create a 404 HTTPException with a consistent detail message."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
