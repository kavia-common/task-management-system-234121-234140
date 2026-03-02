from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def get_user_by_email(db: Session, email: str) -> dict | None:
    """Fetch a user by email (case-insensitive via citext)."""
    row = db.execute(
        text(
            """
            SELECT id::text AS id, email::text AS email, password_hash, display_name
            FROM users
            WHERE email = :email
            """
        ),
        {"email": email},
    ).mappings().first()
    return dict(row) if row else None


# PUBLIC_INTERFACE
def get_user_by_id(db: Session, user_id: str) -> dict | None:
    """Fetch a user by id."""
    row = db.execute(
        text(
            """
            SELECT id::text AS id, email::text AS email, password_hash, display_name
            FROM users
            WHERE id = :id
            """
        ),
        {"id": user_id},
    ).mappings().first()
    return dict(row) if row else None


# PUBLIC_INTERFACE
def create_user(db: Session, email: str, password_hash: str, display_name: str | None) -> dict:
    """Create a new user and return profile fields."""
    row = db.execute(
        text(
            """
            INSERT INTO users (email, password_hash, display_name)
            VALUES (:email, :password_hash, :display_name)
            RETURNING id::text AS id, email::text AS email, display_name
            """
        ),
        {"email": email, "password_hash": password_hash, "display_name": display_name},
    ).mappings().one()
    db.commit()
    return dict(row)
