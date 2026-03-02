from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.routers.auth import router as auth_router
from src.api.routers.tags import router as tags_router
from src.api.routers.tasks import router as tasks_router

openapi_tags = [
    {"name": "Auth", "description": "Authentication endpoints (register/login/me/logout)."},
    {"name": "Tasks", "description": "Task CRUD and query endpoints."},
    {"name": "Tags", "description": "User tags endpoints (list/search)."},
]

app = FastAPI(
    title="Task Manager API",
    description="FastAPI backend for task management: authentication, tasks, tags, and query capabilities.",
    version="0.3.0",
    openapi_tags=openapi_tags,
)

allow_origins = [o.strip() for o in settings.cors_allow_origins.split(",")] if settings.cors_allow_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(tags_router)


@app.get("/", tags=["Health"], summary="Health check", operation_id="health_check")
def health_check() -> dict:
    """Health check endpoint.

    Returns:
        JSON payload indicating server is healthy.
    """
    return {"message": "Healthy"}
