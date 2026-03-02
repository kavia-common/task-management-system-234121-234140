from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TaskStatus = Literal["todo", "in_progress", "done", "archived"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


class TaskOut(BaseModel):
    """Task returned to the frontend."""

    id: str = Field(..., description="Task id (UUID).")
    title: str = Field(..., description="Title.")
    description: str | None = Field(None, description="Optional description.")
    status: TaskStatus = Field(..., description="Status.")
    priority: TaskPriority = Field(..., description="Priority.")
    due_date: str | None = Field(None, description="Due date ISO string (or null).")
    created_at: str = Field(..., description="Created timestamp ISO string.")
    updated_at: str = Field(..., description="Updated timestamp ISO string.")
    tags: list[str] = Field(default_factory=list, description="Tag names attached to task.")


class TaskCreateIn(BaseModel):
    """Create task payload (aligned with frontend)."""

    title: str = Field(..., description="Title.", min_length=1, max_length=200)
    description: str | None = Field(None, description="Optional description.")
    status: TaskStatus = Field(..., description="Status.")
    priority: TaskPriority = Field(..., description="Priority.")
    due_date: str | None = Field(None, description="Due date ISO string (or null).")
    tags: list[str] = Field(default_factory=list, description="Tag names.")


class TaskUpdateIn(BaseModel):
    """Update task payload (partial)."""

    title: str | None = Field(None, description="Title.", min_length=1, max_length=200)
    description: str | None = Field(None, description="Optional description.")
    status: TaskStatus | None = Field(None, description="Status.")
    priority: TaskPriority | None = Field(None, description="Priority.")
    due_date: str | None = Field(None, description="Due date ISO string (or null).")
    tags: list[str] | None = Field(None, description="Full tag list replacement (tag names).")


class TaskListQuery(BaseModel):
    """Query params for listing tasks."""

    q: str | None = Field(None, description="Search query over title/description.")
    status: TaskStatus | None = Field(None, description="Filter by status.")
    priority: TaskPriority | None = Field(None, description="Filter by priority.")
    tag: str | None = Field(None, description="Filter tasks that have a tag (by name).")
    sort: Literal["updated_desc", "updated_asc", "due_asc", "due_desc", "priority_desc"] | None = Field(
        None,
        description="Sort order.",
    )


def _parse_iso(dt: str) -> datetime:
    # Used only for server-side validation; endpoints convert to timestamptz for DB.
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))
