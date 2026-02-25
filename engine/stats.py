"""Compute episode stats from game results."""

from __future__ import annotations

from engine.models import GameResult, Role


def compute_episode_stats(games: list[GameResult]) -> dict:
    """Aggregate stats across all games in an episode."""
    player_stats: dict[str, dict] = {}

    for game in games:
        for player in game.players:
            name = player.name
            if name not in player_stats:
                player_stats[name] = {
                    "games_played": 0,
                    "times_mafia": 0,
                    "times_town": 0,
                    "wins": 0,
                    "wins_as_mafia": 0,
                    "wins_as_town": 0,
                    "times_eliminated": 0,
                    "times_first_eliminated": 0,
                    "votes_received": 0,
                    "votes_cast_correctly": 0,  # voted for mafia when town
                }

            stats = player_stats[name]
            stats["games_played"] += 1

            is_mafia = player.role == Role.MAFIA
            if is_mafia:
                stats["times_mafia"] += 1
            else:
                stats["times_town"] += 1

            won = (is_mafia and game.winner == "mafia") or (
                not is_mafia and game.winner == "town"
            )
            if won:
                stats["wins"] += 1
                if is_mafia:
                    stats["wins_as_mafia"] += 1
                else:
                    stats["wins_as_town"] += 1

        # Track eliminations and votes
        for i, round_data in enumerate(game.rounds):
            if round_data.eliminated:
                player_stats[round_data.eliminated]["times_eliminated"] += 1
                if i == 0:
                    player_stats[round_data.eliminated]["times_first_eliminated"] += 1

            for vote in round_data.votes:
                if vote.target in player_stats:
                    player_stats[vote.target]["votes_received"] += 1
                # Check if town player voted for mafia
                voter_info = next(
                    (p for p in game.players if p.name == vote.voter), None
                )
                if voter_info and voter_info.role == Role.TOWN and vote.target == game.mafia_player:
                    player_stats[vote.voter]["votes_cast_correctly"] += 1

    # Compute derived stats
    for name, stats in player_stats.items():
        stats["win_rate"] = (
            round(stats["wins"] / stats["games_played"] * 100, 1)
            if stats["games_played"] > 0
            else 0
        )
        stats["mafia_win_rate"] = (
            round(stats["wins_as_mafia"] / stats["times_mafia"] * 100, 1)
            if stats["times_mafia"] > 0
            else 0
        )
        stats["town_win_rate"] = (
            round(stats["wins_as_town"] / stats["times_town"] * 100, 1)
            if stats["times_town"] > 0
            else 0
        )
        stats["detection_rate"] = (
            round(stats["votes_cast_correctly"] / stats["times_town"] * 100, 1)
            if stats["times_town"] > 0
            else 0
        )

    # Superlatives
    superlatives = {}
    if player_stats:
        superlatives["best_liar"] = max(
            player_stats, key=lambda n: player_stats[n]["mafia_win_rate"]
        )
        superlatives["best_detective"] = max(
            player_stats, key=lambda n: player_stats[n]["detection_rate"]
        )
        superlatives["first_to_die"] = max(
            player_stats, key=lambda n: player_stats[n]["times_first_eliminated"]
        )
        superlatives["most_sus"] = max(
            player_stats, key=lambda n: player_stats[n]["votes_received"]
        )

    return {
        "players": player_stats,
        "superlatives": superlatives,
        "total_games": len(games),
        "town_wins": sum(1 for g in games if g.winner == "town"),
        "mafia_wins": sum(1 for g in games if g.winner == "mafia"),
    }
