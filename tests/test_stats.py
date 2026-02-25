"""Tests for stats computation."""

from engine.games.mafia import run_episode
from engine.models import GameResult, PlayerInfo, Role, RoundResult, Vote
from engine.stats import compute_episode_stats


class TestStatsComputation:
    def test_basic_stats(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=5, episode_id="stats-test")
        stats = compute_episode_stats(results)

        assert stats["total_games"] == 5
        assert stats["town_wins"] + stats["mafia_wins"] == 5

    def test_all_players_present(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=5, episode_id="stats-test")
        stats = compute_episode_stats(results)

        for name in ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]:
            assert name in stats["players"]
            ps = stats["players"][name]
            assert ps["games_played"] == 5

    def test_win_rates_bounded(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=10, episode_id="stats-test")
        stats = compute_episode_stats(results)

        for ps in stats["players"].values():
            assert 0 <= ps["win_rate"] <= 100
            assert 0 <= ps["mafia_win_rate"] <= 100
            assert 0 <= ps["town_win_rate"] <= 100
            assert 0 <= ps["detection_rate"] <= 100

    def test_mafia_town_games_add_up(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=10, episode_id="stats-test")
        stats = compute_episode_stats(results)

        for ps in stats["players"].values():
            assert ps["times_mafia"] + ps["times_town"] == ps["games_played"]

    def test_wins_dont_exceed_games(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=10, episode_id="stats-test")
        stats = compute_episode_stats(results)

        for ps in stats["players"].values():
            assert ps["wins"] <= ps["games_played"]
            assert ps["wins_as_mafia"] <= ps["times_mafia"]
            assert ps["wins_as_town"] <= ps["times_town"]

    def test_detection_rate_is_per_vote(self, default_mock_players):
        """Detection rate should be votes_cast_for_mafia / total_votes_cast_as_town."""
        results = run_episode(default_mock_players, num_games=5, episode_id="stats-test")
        stats = compute_episode_stats(results)

        for ps in stats["players"].values():
            total_town_votes = ps["total_votes_cast_as_town"]
            correct_votes = ps["votes_cast_for_mafia"]
            if total_town_votes > 0:
                expected = round(correct_votes / total_town_votes * 100, 1)
                assert ps["detection_rate"] == expected


class TestSuperlatives:
    def test_all_superlatives_present(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=10, episode_id="stats-test")
        stats = compute_episode_stats(results)

        expected_keys = {"best_liar", "best_detective", "first_to_die", "most_sus", "survivor"}
        assert set(stats["superlatives"].keys()) == expected_keys

    def test_superlatives_are_valid_players(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=10, episode_id="stats-test")
        stats = compute_episode_stats(results)

        valid_names = {"Claude", "GPT", "Gemini", "DeepSeek", "Llama"}
        for name in stats["superlatives"].values():
            assert name in valid_names


class TestStatsEdgeCases:
    def test_single_game(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=1, episode_id="edge")
        stats = compute_episode_stats(results)
        assert stats["total_games"] == 1

    def test_empty_games(self):
        stats = compute_episode_stats([])
        assert stats["total_games"] == 0
        assert stats["town_wins"] == 0
        assert stats["mafia_wins"] == 0
        assert stats["players"] == {}
        assert stats["superlatives"] == {}

    def test_avg_survival_present(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=5, episode_id="stats-test")
        stats = compute_episode_stats(results)

        for ps in stats["players"].values():
            assert "avg_survival" in ps
            assert ps["avg_survival"] >= 1  # Everyone survives at least round 1
