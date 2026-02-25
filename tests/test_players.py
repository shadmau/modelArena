"""Tests for LLM player adapters."""

import json

import pytest

from engine.models import PlayerInfo
from engine.players.llm_player import _parse_json_response, _fallback_response
from engine.players.mock_player import MockLLMPlayer


class TestJsonParsing:
    def test_plain_json(self):
        result = _parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_code_fence(self):
        result = _parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_json_with_plain_code_fence(self):
        result = _parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        result = _parse_json_response('Here is my response: {"key": "value"} hope that helps')
        assert result == {"key": "value"}

    def test_nested_json(self):
        text = '{"outer": {"inner": "value"}, "list": [1, 2]}'
        result = _parse_json_response(text)
        assert result["outer"]["inner"] == "value"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("not json at all")

    def test_empty_string_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("")


class TestFallbackResponse:
    def test_contains_required_keys(self):
        result = _fallback_response("TestPlayer")
        assert "public_statement" in result
        assert "private_reasoning" in result
        assert "vote" in result

    def test_contains_player_name(self):
        result = _fallback_response("Claude")
        assert "Claude" in result["public_statement"]


class TestMockPlayer:
    def test_town_discussion(self):
        player = MockLLMPlayer(PlayerInfo(name="Claude", model="mock"))
        response = player.call(
            "You are Claude. You are TOWN.",
            "ROUND 1 — DISCUSSION\nPlayers still alive: Claude, GPT, Gemini\nThis is the first round.",
        )
        assert "public_statement" in response
        assert "private_reasoning" in response
        assert len(response["public_statement"]) > 0
        assert len(response["private_reasoning"]) > 0

    def test_mafia_discussion(self):
        player = MockLLMPlayer(PlayerInfo(name="GPT", model="mock"))
        response = player.call(
            "You are GPT. You are the MAFIA. You must deceive the other players.",
            "ROUND 1 — DISCUSSION\nPlayers still alive: Claude, GPT, Gemini\nThis is the first round.",
        )
        assert "public_statement" in response
        assert "private_reasoning" in response

    def test_voting(self):
        player = MockLLMPlayer(PlayerInfo(name="Claude", model="mock"))
        response = player.call(
            "You are Claude. You are TOWN.",
            "ROUND 1 — TIME TO VOTE\nPlayers alive: Claude, GPT, Gemini\nVote now.",
        )
        assert "vote" in response
        assert response["vote"] in ["GPT", "Gemini"]  # Not Claude (self)
        assert "reasoning" in response

    def test_mock_player_never_crashes(self):
        """Mock should handle any input without raising."""
        player = MockLLMPlayer(PlayerInfo(name="Test", model="mock"))
        for prompt in ["", "garbage", "no players listed", "VOTING but no names"]:
            response = player.call("system", prompt)
            assert isinstance(response, dict)
