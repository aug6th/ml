"""Leaderboard schema models."""
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class LeaderboardEntry(BaseModel):
    """Leaderboard entry schema with optimized Pydantic v2 config."""

    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., min_length=1, max_length=100, description="Username")
    score: int = Field(..., ge=0, description="User score")
    rank: int | None = Field(None, ge=1, description="User rank")
    created_at: datetime | None = Field(None, description="Entry creation timestamp")

