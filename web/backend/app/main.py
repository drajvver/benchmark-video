"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.routers import results, leaderboard

app = FastAPI(
    title="Video Benchmark API",
    description="API for video encoding benchmark results",
    version="1.0.0",
)

# CORS
# When wildcard "*" is used with allow_credentials=True, Starlette's default
# behaviour is buggy: it returns "Access-Control-Allow-Origin: *" for simple
# requests that carry an Authorization header (not a cookie). Browsers reject
# this. Using allow_origin_regex=".*" instead forces Starlette to echo back
# the actual origin, which works correctly with credentials.
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

# Include routers
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
