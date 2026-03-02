from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.core.errors import not_found
from src.dependencies.auth import get_current_user
from src.repositories.tasks import create_task, delete_task, get_task, list_tasks, update_task
from src.schemas.tasks import TaskCreateIn, TaskOut, TaskUpdateIn

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _parse_due_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    # Accept "Z" and offset-aware ISO. Postgres expects timestamptz.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@router.get(
    "",
    response_model=list[TaskOut],
    summary="List tasks",
    description="List current user's tasks with optional search/filter/sort.",
    operation_id="tasks_list",
)
def list_tasks_endpoint(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: Annotated[str | None, Query(description="Search query over title/description.")] = None,
    status: Annotated[str | None, Query(description="Filter by status (todo/in_progress/done/archived).")] = None,
    priority: Annotated[str | None, Query(description="Filter by priority (low/medium/high/urgent).")] = None,
    tag: Annotated[str | None, Query(description="Filter by tag name.")] = None,
    sort: Annotated[
        str | None,
        Query(description="Sort: updated_desc|updated_asc|due_asc|due_desc|priority_desc"),
    ] = None,
) -> list[TaskOut]:
    """List tasks for the authenticated user."""
    rows = list_tasks(db, user_id=user["id"], q=q, status=status, priority=priority, tag=tag, sort=sort)
    return [TaskOut(**r) for r in rows]


@router.post(
    "",
    response_model=TaskOut,
    summary="Create task",
    description="Create a task for the current user.",
    operation_id="tasks_create",
)
def create_task_endpoint(
    payload: TaskCreateIn,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    """Create a task."""
    row = create_task(
        db,
        user_id=user["id"],
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_at=_parse_due_date(payload.due_date),
        tag_names=payload.tags,
    )
    return TaskOut(**row)


@router.get(
    "/{task_id}",
    response_model=TaskOut,
    summary="Get task",
    description="Get a task by id (must belong to current user).",
    operation_id="tasks_get",
)
def get_task_endpoint(
    task_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    """Get a task by id."""
    row = get_task(db, user_id=user["id"], task_id=task_id)
    if not row:
        raise not_found("Task not found")
    return TaskOut(**row)


@router.patch(
    "/{task_id}",
    response_model=TaskOut,
    summary="Update task",
    description="Patch-update a task (must belong to current user).",
    operation_id="tasks_update",
)
def update_task_endpoint(
    task_id: str,
    payload: TaskUpdateIn,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskOut:
    """Update a task."""
    row = update_task(
        db,
        user_id=user["id"],
        task_id=task_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_at=_parse_due_date(payload.due_date),
        tags=payload.tags,
    )
    if not row:
        raise not_found("Task not found")
    return TaskOut(**row)


@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Delete a task by id (must belong to current user).",
    operation_id="tasks_delete",
)
def delete_task_endpoint(
    task_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a task."""
    ok = delete_task(db, user_id=user["id"], task_id=task_id)
    if not ok:
        raise not_found("Task not found")
    return {"ok": True}
