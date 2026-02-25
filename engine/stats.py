"""Compute episode stats from game results."""

from __future__ import annotations

from engine.models import GameResult, Role


def compute_episode_stats(games: list[GameResult]) -> dict:
    """Aggregate stats across all games in an episode."""
    player_stats: dict[str, dict] = {}

    for game in games:
        # Build lookup for this game
        player_roles = {p.name: p.role for p in game.players}

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
                    "votes_received_total": 0,
                    "votes_cast_for_mafia": 0,  # correct votes (as town, voted for mafia)
                    "total_votes_cast_as_town": 0,  # total voting rounds as town
                    "survived_rounds_total": 0,
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

        # Track per-round data
        alive_at_round_start = {p.name for p in game.players}

        for i, round_data in enumerate(game.rounds):
            # Track survival
            for name in alive_at_round_start:
                if name in player_stats:
                    player_stats[name]["survived_rounds_total"] += 1

            # Track eliminations
            if round_data.eliminated:
                player_stats[round_data.eliminated]["times_eliminated"] += 1
                if i == 0:
                    player_stats[round_data.eliminated]["times_first_eliminated"] += 1
                alive_at_round_start.discard(round_data.eliminated)

            # Track votes
            for vote in round_data.votes:
                if vote.target in player_stats:
                    player_stats[vote.target]["votes_received_total"] += 1

                # Track correct votes: town player voted for actual mafia
                voter_role = player_roles.get(vote.voter)
                if voter_role == Role.TOWN:
                    player_stats[vote.voter]["total_votes_cast_as_town"] += 1
                    if vote.target == game.mafia_player:
                        player_stats[vote.voter]["votes_cast_for_mafia"] += 1

    # Compute derived stats
    for name, stats in player_stats.items():
        gp = stats["games_played"]
        stats["win_rate"] = _pct(stats["wins"], gp)
        stats["mafia_win_rate"] = _pct(stats["wins_as_mafia"], stats["times_mafia"])
        stats["town_win_rate"] = _pct(stats["wins_as_town"], stats["times_town"])

        # Detection rate: % of votes (as town) that correctly targeted mafia
        stats["detection_rate"] = _pct(
            stats["votes_cast_for_mafia"], stats["total_votes_cast_as_town"]
        )

        # Average rounds survived per game
        stats["avg_survival"] = (
            round(stats["survived_rounds_total"] / gp, 1) if gp > 0 else 0
        )

    # Superlatives
    superlatives = _compute_superlatives(player_stats)

    return {
        "players": player_stats,
        "superlatives": superlatives,
        "total_games": len(games),
        "town_wins": sum(1 for g in games if g.winner == "town"),
        "mafia_wins": sum(1 for g in games if g.winner == "mafia"),
    }


def _pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 1) if denominator > 0 else 0.0


def _compute_superlatives(player_stats: dict[str, dict]) -> dict[str, str]:
    if not player_stats:
        return {}

    return {
        "best_liar": max(player_stats, key=lambda n: player_stats[n]["mafia_win_rate"]),
        "best_detective": max(player_stats, key=lambda n: player_stats[n]["detection_rate"]),
        "first_to_die": max(player_stats, key=lambda n: player_stats[n]["times_first_eliminated"]),
        "most_sus": max(player_stats, key=lambda n: player_stats[n]["votes_received_total"]),
        "survivor": max(player_stats, key=lambda n: player_stats[n]["avg_survival"]),
    }
