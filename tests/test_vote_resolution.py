"""Tests for vote target resolution (fuzzy matching)."""

from engine.games.mafia import MafiaGame
from engine.models import PlayerInfo
from engine.players.mock_player import MockLLMPlayer


def make_game() -> MafiaGame:
    players = [
        MockLLMPlayer(PlayerInfo(name=n, model="mock"))
        for n in ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]
    ]
    return MafiaGame(players)


class TestVoteResolution:
    def test_exact_match(self):
        game = make_game()
        assert game._resolve_vote_target("GPT", ["Claude", "GPT", "Gemini"]) == "GPT"

    def test_case_insensitive(self):
        game = make_game()
        assert game._resolve_vote_target("gpt", ["Claude", "GPT", "Gemini"]) == "GPT"
        assert game._resolve_vote_target("CLAUDE", ["Claude", "GPT"]) == "Claude"
        assert game._resolve_vote_target("deepseek", ["DeepSeek", "Llama"]) == "DeepSeek"

    def test_normalized_match(self):
        game = make_game()
        assert game._resolve_vote_target("deep seek", ["DeepSeek", "Llama"]) == "DeepSeek"
        assert game._resolve_vote_target("Deep-Seek", ["DeepSeek", "Llama"]) == "DeepSeek"
        assert game._resolve_vote_target("deep_seek", ["DeepSeek", "Llama"]) == "DeepSeek"

    def test_substring_match(self):
        game = make_game()
        assert game._resolve_vote_target("Deep", ["DeepSeek", "Llama"]) == "DeepSeek"

    def test_no_match_returns_valid_target(self):
        game = make_game()
        result = game._resolve_vote_target("NonExistent", ["Claude", "GPT"])
        assert result in ["Claude", "GPT"]

    def test_empty_target_returns_valid(self):
        game = make_game()
        result = game._resolve_vote_target("", ["Claude", "GPT"])
        assert result in ["Claude", "GPT"]
