"""Tests for stats computation."""

from unittest.mock import patch

from engine.games.mafia import run_episode
from engine.models import PlayerInfo
from engine.players.llm_player import LLMPlayer
from engine.stats import compute_episode_stats
from tests.test_mafia import make_mock_players, mock_call_factory


class TestStats:
    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_stats_computed(self):
        players = make_mock_players()
        results = run_episode(players, num_games=5, episode_id="stats-test")
        stats = compute_episode_stats(results)

        assert stats["total_games"] == 5
        assert stats["town_wins"] + stats["mafia_wins"] == 5
        assert "players" in stats
        assert "superlatives" in stats

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_all_players_have_stats(self):
        players = make_mock_players()
        results = run_episode(players, num_games=5, episode_id="stats-test2")
        stats = compute_episode_stats(results)

        for name in ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]:
            assert name in stats["players"]
            ps = stats["players"][name]
            assert ps["games_played"] == 5
            assert "win_rate" in ps
            assert "mafia_win_rate" in ps
            assert "town_win_rate" in ps

    @patch.object(LLMPlayer, "call", mock_call_factory())
    def test_superlatives_exist(self):
        players = make_mock_players()
        results = run_episode(players, num_games=5, episode_id="stats-test3")
        stats = compute_episode_stats(results)

        for key in ["best_liar", "best_detective", "first_to_die", "most_sus"]:
            assert key in stats["superlatives"]
            assert stats["superlatives"][key] in ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]
