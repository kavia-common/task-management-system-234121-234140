from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.dependencies.auth import get_current_user

router = APIRouter(prefix="/tags", tags=["Tags"])


class TagOut(BaseModel):
    """Tag returned to frontend."""

    id: str = Field(..., description="Tag id (UUID).")
    name: str = Field(..., description="Tag name.")
    color: str | None = Field(None, description="Optional color.")


@router.get(
    "",
    response_model=list[TagOut],
    summary="List tags",
    description="List current user's tags (supports optional search query).",
    operation_id="tags_list",
)
def list_tags(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="Optional search query over tag name."),
) -> list[TagOut]:
    """List tags for the authenticated user."""
    rows = db.execute(
        text(
            """
            SELECT id::text AS id, name, color
            FROM tags
            WHERE user_id = :user_id
              AND (:q IS NULL OR name ILIKE '%' || :q || '%')
            ORDER BY lower(name) ASC
            LIMIT 100
            """
        ),
        {"user_id": user["id"], "q": q},
    ).mappings().all()
    return [TagOut(**dict(r)) for r in rows]
