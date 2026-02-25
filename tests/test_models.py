"""Tests for data models."""

import json

from engine.models import (
    EpisodeResult,
    GameResult,
    PlayerInfo,
    Role,
    RoundResult,
    Statement,
    Vote,
)


class TestPlayerInfo:
    def test_defaults(self):
        p = PlayerInfo(name="Claude", model="anthropic/claude-sonnet-4-20250514")
        assert p.alive is True
        assert p.role is None
        assert p.avatar_color == ""

    def test_role_assignment(self):
        p = PlayerInfo(name="GPT", model="openai/gpt-4o", role=Role.MAFIA)
        assert p.role == Role.MAFIA

    def test_model_copy_is_independent(self):
        p = PlayerInfo(name="Claude", model="test", role=Role.TOWN, alive=True)
        copy = p.model_copy()
        copy.alive = False
        copy.role = Role.MAFIA
        assert p.alive is True
        assert p.role == Role.TOWN


class TestStatement:
    def test_creation(self):
        s = Statement(
            player="Claude",
            public_text="I suspect GPT",
            private_reasoning="Analyzing behavior",
            round_number=1,
        )
        assert s.player == "Claude"
        assert s.round_number == 1

    def test_serialization(self):
        s = Statement(
            player="GPT",
            public_text="I'm innocent",
            private_reasoning="I need to lie",
            round_number=2,
        )
        data = json.loads(s.model_dump_json())
        assert data["player"] == "GPT"
        assert data["round_number"] == 2


class TestVote:
    def test_creation(self):
        v = Vote(voter="Claude", target="GPT", reasoning="Suspicious")
        assert v.voter == "Claude"
        assert v.target == "GPT"


class TestRoundResult:
    def test_empty_round(self):
        r = RoundResult(round_number=1, phase="full")
        assert r.eliminated is None
        assert len(r.statements) == 0
        assert len(r.votes) == 0

    def test_round_with_data(self):
        r = RoundResult(
            round_number=1,
            phase="full",
            statements=[Statement(player="Claude", public_text="hi", private_reasoning="hmm", round_number=1)],
            votes=[Vote(voter="Claude", target="GPT", reasoning="sus")],
            eliminated="GPT",
            eliminated_role=Role.MAFIA,
        )
        assert r.eliminated == "GPT"
        assert r.eliminated_role == Role.MAFIA
        assert len(r.statements) == 1
        assert len(r.votes) == 1


class TestGameResult:
    def test_serialization_roundtrip(self):
        game = GameResult(
            game_id="test-001",
            players=[
                PlayerInfo(name="Claude", model="test", role=Role.TOWN),
                PlayerInfo(name="GPT", model="test", role=Role.MAFIA),
            ],
            winner="town",
            mafia_player="GPT",
            total_rounds=3,
        )
        json_str = game.model_dump_json()
        data = json.loads(json_str)
        reconstructed = GameResult(**data)
        assert reconstructed.game_id == "test-001"
        assert reconstructed.winner == "town"
        assert len(reconstructed.players) == 2

    def test_defaults(self):
        game = GameResult(game_id="x")
        assert game.game_type == "mafia"
        assert game.winner == ""
        assert game.total_rounds == 0


class TestEpisodeResult:
    def test_creation(self):
        ep = EpisodeResult(episode_id="ep001", episode_title="Test")
        assert ep.game_type == "mafia"
        assert len(ep.games) == 0

    def test_with_games(self):
        game = GameResult(game_id="g1", winner="town", mafia_player="GPT", total_rounds=1)
        ep = EpisodeResult(episode_id="ep001", episode_title="Test", games=[game])
        assert len(ep.games) == 1
        assert ep.games[0].game_id == "g1"
