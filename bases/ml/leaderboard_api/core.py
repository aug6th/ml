"""Leaderboard API base."""
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, Query

from ml import auth, config, leaderboard, logging, middleware
from ml.fastapilite import create_app
from ml.schema import LeaderboardEntry

settings = config.get_settings()
logger = logging.get_logger("leaderboard-FastAPI-logger")


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting up ml Leaderboard API")
    yield
    logger.info("Shutting down ml Leaderboard API")


app = create_app(
    title="ml Leaderboard API",
    description="A Python Polylith project template",
    version="0.1.0",
)
app.router.lifespan_context = lifespan
middleware.setup_middleware(app)


def _to_domain_entry(entry: LeaderboardEntry) -> leaderboard.Entry:
    """Convert schema entry to domain entry."""
    return leaderboard.Entry(
        user_id=entry.user_id,
        username=entry.username,
        score=entry.score,
        rank=entry.rank,
        created_at=entry.created_at,
    )


def _to_schema_entry(entry: leaderboard.Entry) -> LeaderboardEntry:
    """Convert domain entry to schema entry efficiently."""
    return LeaderboardEntry(
        user_id=entry.user_id,
        username=entry.username,
        score=entry.score,
        rank=entry.rank,
        created_at=entry.created_at,
    )


@app.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    limit: Annotated[int, Query(ge=1, le=100, description="Number of entries to return")] = 10,
) -> list[LeaderboardEntry]:
    """Get top leaderboard entries (async for better concurrency)."""
    entries = leaderboard.get_top_entries(limit=limit)
    return [_to_schema_entry(entry) for entry in entries]


@app.post("/leaderboard", response_model=LeaderboardEntry)
async def add_entry(
    entry: LeaderboardEntry,
    current_user: Annotated[dict[str, str], Depends(auth.get_current_user)],
) -> LeaderboardEntry:
    """Add a new leaderboard entry (requires authentication)."""
    logger.info("Adding leaderboard entry for user=%s", entry.user_id)
    domain_entry = _to_domain_entry(entry)
    leaderboard.add_entry(domain_entry)
    return entry
