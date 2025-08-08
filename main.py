from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import task_router
from app.database import init_db

from typing import Dict, Any


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield


app = FastAPI(
    title="Task Management API",
    description="A comprehensive task management system with full relationship support",
    version="1.0.0",
    debug=True,
    lifespan=lifespan,
)


@app.get("/", tags=["Root"])
def read_root() -> Dict[str, Any]:
    return {
        "message": "Welcome to Task Management API!",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": [
            "User management",
            "Project management",
            "Task management with relationships",
            "Tags and comments",
            "Full CRUD operations",
        ],
    }


# Include routers
app.include_router(
    router=task_router.router,
    prefix="/tasks",
    tags=["Tasks"],
)
