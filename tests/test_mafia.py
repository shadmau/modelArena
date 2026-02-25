"""Tests for Mafia game logic using mock players."""

from __future__ import annotations

import json

import pytest

from engine.games.mafia import MafiaGame, run_episode
from engine.models import PlayerInfo, Role
from engine.players.mock_player import MockLLMPlayer


class TestMafiaGameBasics:
    def test_game_completes(self, default_mock_players):
        game = MafiaGame(default_mock_players, game_id="test-001")
        result = game.run(mafia_player="GPT")

        assert result.game_id == "test-001"
        assert result.winner in ("town", "mafia")
        assert result.mafia_player == "GPT"
        assert result.total_rounds >= 1
        assert len(result.rounds) >= 1

    def test_roles_assigned_correctly(self, default_mock_players):
        game = MafiaGame(default_mock_players, game_id="test-002")
        result = game.run(mafia_player="Claude")

        mafia_count = sum(1 for p in result.players if p.role == Role.MAFIA)
        town_count = sum(1 for p in result.players if p.role == Role.TOWN)
        assert mafia_count == 1
        assert town_count == 4
        assert result.mafia_player == "Claude"

    def test_random_mafia_assignment(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run()
        assert result.mafia_player in ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]

    def test_invalid_mafia_player_falls_back_to_random(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run(mafia_player="NonExistent")
        assert result.mafia_player in ["Claude", "GPT", "Gemini", "DeepSeek", "Llama"]

    def test_minimum_players_enforced(self):
        players = [MockLLMPlayer(PlayerInfo(name=n, model="mock")) for n in ["A", "B", "C"]]
        with pytest.raises(ValueError, match="at least 4"):
            MafiaGame(players)

    def test_four_players_works(self, four_mock_players):
        game = MafiaGame(four_mock_players)
        result = game.run()
        assert result.winner in ("town", "mafia")


class TestMafiaGameContent:
    def test_statements_captured(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run()

        first_round = result.rounds[0]
        # All 5 alive players should have statements
        assert len(first_round.statements) == 5
        for stmt in first_round.statements:
            assert len(stmt.public_text) > 0
            assert len(stmt.private_reasoning) > 0
            assert stmt.round_number == 1

    def test_all_alive_players_speak(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run()

        first_round = result.rounds[0]
        speakers = {s.player for s in first_round.statements}
        assert speakers == {"Claude", "GPT", "Gemini", "DeepSeek", "Llama"}

    def test_votes_captured(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run()

        first_round = result.rounds[0]
        assert len(first_round.votes) == 5
        for vote in first_round.votes:
            assert vote.voter != vote.target  # Can't self-vote
            assert len(vote.reasoning) > 0

    def test_eliminated_player_doesnt_speak_next_round(self, default_mock_players):
        """If a game goes 2+ rounds, eliminated players should not appear."""
        game = MafiaGame(default_mock_players)
        result = game.run()

        if len(result.rounds) >= 2:
            eliminated_in_r1 = result.rounds[0].eliminated
            if eliminated_in_r1:
                r2_speakers = {s.player for s in result.rounds[1].statements}
                assert eliminated_in_r1 not in r2_speakers

    def test_eliminated_player_doesnt_vote_next_round(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run()

        if len(result.rounds) >= 2:
            eliminated_in_r1 = result.rounds[0].eliminated
            if eliminated_in_r1:
                r2_voters = {v.voter for v in result.rounds[1].votes}
                assert eliminated_in_r1 not in r2_voters


class TestMafiaWinConditions:
    def test_town_wins_when_mafia_eliminated(self, default_mock_players):
        """Run many games, verify town win condition is correct."""
        for _ in range(20):
            game = MafiaGame(default_mock_players)
            result = game.run()
            if result.winner == "town":
                # Mafia should be eliminated
                alive_at_end = [p.name for p in result.players if p.alive]
                assert result.mafia_player not in alive_at_end
                return
        # If we ran 20 games and never got a town win, that's unlikely but not impossible

    def test_mafia_wins_with_two_remaining(self, default_mock_players):
        """Run many games, verify mafia win condition is correct."""
        for _ in range(20):
            game = MafiaGame(default_mock_players)
            result = game.run()
            if result.winner == "mafia":
                alive_at_end = [p.name for p in result.players if p.alive]
                assert len(alive_at_end) <= 2
                assert result.mafia_player in alive_at_end
                return

    def test_game_doesnt_exceed_10_rounds(self, default_mock_players):
        for _ in range(10):
            game = MafiaGame(default_mock_players)
            result = game.run()
            assert result.total_rounds <= 10


class TestMafiaGameState:
    def test_game_result_serializable(self, default_mock_players):
        game = MafiaGame(default_mock_players)
        result = game.run()

        json_str = result.model_dump_json()
        data = json.loads(json_str)
        assert "game_id" in data
        assert "rounds" in data
        assert "winner" in data
        assert "mafia_player" in data

    def test_multiple_games_independent(self, default_mock_players):
        """Running multiple games with same players should not leak state."""
        results = []
        for i in range(3):
            game = MafiaGame(default_mock_players, game_id=f"ind-{i}")
            result = game.run()
            results.append(result)

        # Each game should start fresh
        for result in results:
            assert result.rounds[0].round_number == 1
            alive_in_r1 = {s.player for s in result.rounds[0].statements}
            assert len(alive_in_r1) == 5  # All players alive at start

    def test_player_info_copied_not_shared(self, default_mock_players):
        """GameResult should contain copies of PlayerInfo, not references."""
        game = MafiaGame(default_mock_players)
        result = game.run()

        # Modifying result players should not affect the game's players
        result.players[0].alive = False
        result.players[0].role = Role.MAFIA

        # Original player should be unaffected
        original_player = default_mock_players[0]
        # Note: the game DID modify alive/role during play, but the point is
        # that the GameResult has its own copies
        assert result.players[0] is not original_player.info


class TestRunEpisode:
    def test_correct_number_of_games(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=3, episode_id="test-ep")
        assert len(results) == 3

    def test_game_ids_sequential(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=3, episode_id="test-ep")
        assert results[0].game_id == "test-ep-001"
        assert results[1].game_id == "test-ep-002"
        assert results[2].game_id == "test-ep-003"

    def test_every_model_plays_mafia_at_least_once(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=10, episode_id="test")
        mafia_players = {r.mafia_player for r in results}
        expected = {"Claude", "GPT", "Gemini", "DeepSeek", "Llama"}
        assert expected.issubset(mafia_players)

    def test_all_games_have_winner(self, default_mock_players):
        results = run_episode(default_mock_players, num_games=5, episode_id="test")
        for r in results:
            assert r.winner in ("town", "mafia")
