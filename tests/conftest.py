"""Shared test fixtures."""

import pytest

from engine.models import PlayerInfo
from engine.players.mock_player import MockLLMPlayer


@pytest.fixture
def default_mock_players() -> list[MockLLMPlayer]:
    """5 default mock players."""
    names_models = [
        ("Claude", "mock/claude"),
        ("GPT", "mock/gpt"),
        ("Gemini", "mock/gemini"),
        ("DeepSeek", "mock/deepseek"),
        ("Llama", "mock/llama"),
    ]
    return [
        MockLLMPlayer(PlayerInfo(name=n, model=m))
        for n, m in names_models
    ]


@pytest.fixture
def four_mock_players() -> list[MockLLMPlayer]:
    """Minimum 4 players for a valid game."""
    return [
        MockLLMPlayer(PlayerInfo(name=n, model=f"mock/{n.lower()}"))
        for n in ["Alice", "Bob", "Charlie", "Diana"]
    ]
