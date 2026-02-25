"""Tests for Mafia game logic using mocked LLM responses."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from engine.games.mafia import MafiaGame, run_episode
from engine.models import PlayerInfo, Role
from engine.players.llm_player import LLMPlayer


def make_mock_players(names: list[str] | None = None) -> list[LLMPlayer]:
    """Create players with mocked LLM call method."""
    if names is None:
        names = ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]

    players = []
    for name in names:
        info = PlayerInfo(name=name, model=f"mock/{name.lower()}")
        player = LLMPlayer(info)
        players.append(player)
    return players


def mock_call_factory():
    """Returns a mock call function that produces valid game responses."""
    def mock_call(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> dict:
        if "VOTING" in user_prompt:
            # Parse alive players from prompt
            alive_line = [l for l in user_prompt.split("\n") if "Players alive:" in l]
            if alive_line:
                alive_str = alive_line[0].split("Players alive:")[1].strip()
                alive = [n.strip() for n in alive_str.split(",")]
                valid = [n for n in alive if n != self.info.name]
            else:
                valid = ["Claude"]
            import random
            target = random.choice(valid) if valid else "Claude"
            return {
                "vote": target,
                "reasoning": f"I suspect {target}",
            }
        else:
            return {
                "public_statement": f"I am {self.info.name} and I'm analyzing the situation.",
                "private_reasoning": f"Thinking about who might be mafia...",
            }
    return mock_call


class TestMafiaGame:
    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_game_completes(self):
        players = make_mock_players()
        game = MafiaGame(players, game_id="test-001")
        result = game.run(mafia_player="GPT")

        assert result.game_id == "test-001"
        assert result.winner in ("town", "mafia")
        assert result.mafia_player == "GPT"
        assert result.total_rounds >= 1
        assert len(result.rounds) >= 1

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_roles_assigned_correctly(self):
        players = make_mock_players()
        game = MafiaGame(players, game_id="test-002")
        result = game.run(mafia_player="Claude")

        mafia_count = sum(1 for p in result.players if p.role == Role.MAFIA)
        town_count = sum(1 for p in result.players if p.role == Role.TOWN)
        assert mafia_count == 1
        assert town_count == 4
        assert result.mafia_player == "Claude"

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_statements_captured(self):
        players = make_mock_players()
        game = MafiaGame(players, game_id="test-003")
        result = game.run()

        first_round = result.rounds[0]
        assert len(first_round.statements) == 5
        for stmt in first_round.statements:
            assert stmt.public_text != ""
            assert stmt.private_reasoning != ""

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_votes_captured(self):
        players = make_mock_players()
        game = MafiaGame(players, game_id="test-004")
        result = game.run()

        first_round = result.rounds[0]
        assert len(first_round.votes) == 5
        for vote in first_round.votes:
            assert vote.voter != vote.target  # Can't self-vote

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_game_result_serializable(self):
        players = make_mock_players()
        game = MafiaGame(players, game_id="test-005")
        result = game.run()

        json_str = result.model_dump_json()
        data = json.loads(json_str)
        assert "game_id" in data
        assert "rounds" in data
        assert "winner" in data

    def test_minimum_players(self):
        players = make_mock_players(["A", "B", "C"])
        with pytest.raises(ValueError, match="at least 4"):
            MafiaGame(players)

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_run_episode(self):
        players = make_mock_players()
        results = run_episode(players, num_games=3, episode_id="test-ep")

        assert len(results) == 3
        for r in results:
            assert r.winner in ("town", "mafia")
            assert r.game_id.startswith("test-ep-")
