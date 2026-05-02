"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.routers import results, leaderboard

app = FastAPI(
    title="Video Benchmark API",
    description="API for video encoding benchmark results",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
if "*" in settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API routers
app.include_router(results.router, prefix=settings.API_PREFIX)
app.include_router(leaderboard.router, prefix=settings.API_PREFIX)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Serve React frontend static files (only if they exist)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(static_dir), html=True),
        name="static",
    )
