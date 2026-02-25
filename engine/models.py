"""Data models for ModelArena game engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    MAFIA = "mafia"
    TOWN = "town"


class PlayerInfo(BaseModel):
    name: str
    model: str
    role: Role | None = None
    alive: bool = True
    avatar_color: str = ""


class Statement(BaseModel):
    player: str
    public_text: str
    private_reasoning: str
    round_number: int


class Vote(BaseModel):
    voter: str
    target: str
    reasoning: str


class RoundResult(BaseModel):
    round_number: int
    phase: str  # "discussion" or "voting"
    statements: list[Statement] = Field(default_factory=list)
    votes: list[Vote] = Field(default_factory=list)
    eliminated: str | None = None
    eliminated_role: Role | None = None


class GameResult(BaseModel):
    game_id: str
    game_type: str = "mafia"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    players: list[PlayerInfo] = Field(default_factory=list)
    rounds: list[RoundResult] = Field(default_factory=list)
    winner: str = ""  # "mafia" or "town"
    mafia_player: str = ""
    total_rounds: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class EpisodeResult(BaseModel):
    episode_id: str
    episode_title: str
    game_type: str = "mafia"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    games: list[GameResult] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
