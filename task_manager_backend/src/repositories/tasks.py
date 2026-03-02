from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_task_row(row: dict) -> dict:
    # v_tasks_with_tags returns tags as jsonb array of objects.
    tags = row.get("tags") or []
    tag_names: list[str] = []
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, dict) and isinstance(t.get("name"), str):
                tag_names.append(t["name"])
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row.get("description"),
        "status": row["status"],
        "priority": row["priority"],
        "due_date": _iso(row.get("due_at")),
        "created_at": _iso(row["created_at"]),
        "updated_at": _iso(row["updated_at"]),
        "tags": tag_names,
    }


# PUBLIC_INTERFACE
def list_tasks(
    db: Session,
    *,
    user_id: str,
    q: str | None,
    status: str | None,
    priority: str | None,
    tag: str | None,
    sort: str | None,
) -> list[dict]:
    """List tasks for a user with optional search/filter/sort (single query via view)."""
    order_by = "updated_at DESC"
    if sort == "updated_asc":
        order_by = "updated_at ASC"
    elif sort == "updated_desc":
        order_by = "updated_at DESC"
    elif sort == "due_asc":
        order_by = "due_at ASC NULLS LAST"
    elif sort == "due_desc":
        order_by = "due_at DESC NULLS LAST"
    elif sort == "priority_desc":
        # Custom order urgent > high > medium > low
        order_by = """CASE priority
            WHEN 'urgent' THEN 4
            WHEN 'high' THEN 3
            WHEN 'medium' THEN 2
            WHEN 'low' THEN 1
            ELSE 0 END DESC, updated_at DESC"""

    sql = f"""
        SELECT
          id::text AS id,
          title,
          description,
          status::text AS status,
          priority::text AS priority,
          due_at,
          created_at,
          updated_at,
          tags
        FROM v_tasks_with_tags
        WHERE user_id = :user_id
          AND (:status IS NULL OR status = :status::task_status)
          AND (:priority IS NULL OR priority = :priority::task_priority)
          AND (
            :q IS NULL
            OR (title ILIKE '%' || :q || '%')
            OR (description ILIKE '%' || :q || '%')
          )
          AND (
            :tag IS NULL
            OR EXISTS (
              SELECT 1
              FROM task_tags tt
              JOIN tags tg ON tg.id = tt.tag_id
              WHERE tt.task_id = v_tasks_with_tags.id
                AND tg.user_id = :user_id
                AND lower(tg.name) = lower(:tag)
            )
          )
        ORDER BY {order_by}
    """

    rows = db.execute(
        text(sql),
        {"user_id": user_id, "q": q, "status": status, "priority": priority, "tag": tag},
    ).mappings().all()
    return [_normalize_task_row(dict(r)) for r in rows]


# PUBLIC_INTERFACE
def get_task(db: Session, *, user_id: str, task_id: str) -> dict | None:
    """Get a single task owned by user."""
    row = db.execute(
        text(
            """
            SELECT
              id::text AS id,
              title,
              description,
              status::text AS status,
              priority::text AS priority,
              due_at,
              created_at,
              updated_at,
              tags
            FROM v_tasks_with_tags
            WHERE user_id = :user_id AND id = :task_id
            """
        ),
        {"user_id": user_id, "task_id": task_id},
    ).mappings().first()
    return _normalize_task_row(dict(row)) if row else None


def _upsert_tags(db: Session, *, user_id: str, names: list[str]) -> list[str]:
    cleaned = []
    for n in names:
        n2 = (n or "").strip()
        if n2 and n2.lower() not in {x.lower() for x in cleaned}:
            cleaned.append(n2)

    if not cleaned:
        return []

    # Ensure tags exist; return canonical names (as inserted/found)
    out: list[str] = []
    for name in cleaned:
        row = db.execute(
            text(
                """
                INSERT INTO tags (user_id, name)
                VALUES (:user_id, :name)
                ON CONFLICT (user_id, lower(name))
                DO UPDATE SET name = EXCLUDED.name
                RETURNING id::text AS id, name
                """
            ),
            {"user_id": user_id, "name": name},
        ).mappings().one()
        out.append(row["name"])
    return out


def _replace_task_tags(db: Session, *, user_id: str, task_id: str, tag_names: list[str]) -> None:
    # Create tags if needed, then map ids, then replace join table.
    _upsert_tags(db, user_id=user_id, names=tag_names)
    db.execute(text("DELETE FROM task_tags WHERE task_id = :task_id"), {"task_id": task_id})

    for name in tag_names:
        row = db.execute(
            text(
                """
                SELECT id::text AS id
                FROM tags
                WHERE user_id = :user_id AND lower(name) = lower(:name)
                """
            ),
            {"user_id": user_id, "name": name},
        ).mappings().first()
        if row:
            db.execute(
                text(
                    """
                    INSERT INTO task_tags (task_id, tag_id)
                    VALUES (:task_id, :tag_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"task_id": task_id, "tag_id": row["id"]},
            )


# PUBLIC_INTERFACE
def create_task(
    db: Session,
    *,
    user_id: str,
    title: str,
    description: str | None,
    status: str,
    priority: str,
    due_at: datetime | None,
    tag_names: list[str],
) -> dict:
    """Create task and set tags."""
    row = db.execute(
        text(
            """
            INSERT INTO tasks (user_id, title, description, status, priority, due_at)
            VALUES (:user_id, :title, :description, :status::task_status, :priority::task_priority, :due_at)
            RETURNING id::text AS id
            """
        ),
        {
            "user_id": user_id,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_at": due_at,
        },
    ).mappings().one()
    task_id = row["id"]
    _replace_task_tags(db, user_id=user_id, task_id=task_id, tag_names=tag_names)
    db.commit()
    # Return via view to include tags + timestamps.
    task = get_task(db, user_id=user_id, task_id=task_id)
    assert task is not None
    return task


# PUBLIC_INTERFACE
def update_task(
    db: Session,
    *,
    user_id: str,
    task_id: str,
    title: str | None,
    description: str | None,
    status: str | None,
    priority: str | None,
    due_at: datetime | None,
    tags: list[str] | None,
) -> dict | None:
    """Update a task (owned by user). Returns updated task or None if missing."""
    existing = db.execute(
        text("SELECT id FROM tasks WHERE id = :task_id AND user_id = :user_id"),
        {"task_id": task_id, "user_id": user_id},
    ).first()
    if not existing:
        return None

    # If marking done, ensure completed_at set. If not done, clear completed_at.
    completed_at = None
    if status == "done":
        completed_at = datetime.now(timezone.utc)
    elif status is not None and status != "done":
        completed_at = None

    db.execute(
        text(
            """
            UPDATE tasks
            SET
              title = COALESCE(:title, title),
              description = COALESCE(:description, description),
              status = COALESCE(:status::task_status, status),
              priority = COALESCE(:priority::task_priority, priority),
              due_at = COALESCE(:due_at, due_at),
              completed_at = CASE
                WHEN :status::task_status IS NULL THEN completed_at
                WHEN :status::task_status = 'done' THEN :completed_at
                ELSE NULL
              END
            WHERE id = :task_id AND user_id = :user_id
            """
        ),
        {
            "task_id": task_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "due_at": due_at,
            "completed_at": completed_at,
        },
    )

    if tags is not None:
        _replace_task_tags(db, user_id=user_id, task_id=task_id, tag_names=tags)

    db.commit()
    updated = get_task(db, user_id=user_id, task_id=task_id)
    return updated


# PUBLIC_INTERFACE
def delete_task(db: Session, *, user_id: str, task_id: str) -> bool:
    """Delete a task owned by user. Returns True if deleted."""
    res = db.execute(
        text("DELETE FROM tasks WHERE id = :task_id AND user_id = :user_id"),
        {"task_id": task_id, "user_id": user_id},
    )
    db.commit()
    return res.rowcount > 0
