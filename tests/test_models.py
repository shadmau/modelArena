"""Tests for data models."""

from engine.models import (
    EpisodeResult,
    GameResult,
    PlayerInfo,
    Role,
    RoundResult,
    Statement,
    Vote,
)


def test_player_info_creation():
    p = PlayerInfo(name="Claude", model="anthropic/claude-sonnet-4-20250514")
    assert p.name == "Claude"
    assert p.alive is True
    assert p.role is None


def test_player_role_assignment():
    p = PlayerInfo(name="GPT", model="openai/gpt-4o", role=Role.MAFIA)
    assert p.role == Role.MAFIA


def test_statement_creation():
    s = Statement(
        player="Claude",
        public_text="I think GPT is suspicious",
        private_reasoning="I'm town, analyzing behavior",
        round_number=1,
    )
    assert s.player == "Claude"
    assert s.round_number == 1


def test_vote_creation():
    v = Vote(voter="Claude", target="GPT", reasoning="Acting suspicious")
    assert v.voter == "Claude"
    assert v.target == "GPT"


def test_round_result():
    r = RoundResult(round_number=1, phase="full")
    assert r.eliminated is None
    assert len(r.statements) == 0


def test_game_result_serialization():
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
    data = game.model_dump()
    assert data["game_id"] == "test-001"
    assert data["winner"] == "town"
    assert len(data["players"]) == 2


def test_episode_result():
    ep = EpisodeResult(
        episode_id="ep001",
        episode_title="Mafia Episode 1",
    )
    assert ep.game_type == "mafia"
    assert len(ep.games) == 0
