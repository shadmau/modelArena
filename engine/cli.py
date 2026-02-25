"""CLI to run ModelArena games."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click

from engine.games.mafia import MafiaGame, run_episode
from engine.models import EpisodeResult
from engine.players.llm_player import LLMPlayer, get_default_players
from engine.stats import compute_episode_stats


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@cli.command()
@click.option("--games", "-n", default=10, help="Number of games to run")
@click.option("--episode-id", "-e", default="ep001", help="Episode ID")
@click.option("--output", "-o", default="results", help="Output directory")
def mafia(games: int, episode_id: str, output: str):
    """Run a Mafia episode with default models."""
    click.echo(f"Running Mafia episode: {episode_id} ({games} games)")

    player_infos = get_default_players()
    players = [LLMPlayer(p) for p in player_infos]

    results = run_episode(players, num_games=games, episode_id=episode_id)

    stats = compute_episode_stats(results)

    episode = EpisodeResult(
        episode_id=episode_id,
        episode_title=f"Mafia — Episode {episode_id}",
        games=results,
        stats=stats,
    )

    # Write output
    out_dir = Path(output) / episode_id
    out_dir.mkdir(parents=True, exist_ok=True)

    episode_file = out_dir / "episode.json"
    episode_file.write_text(episode.model_dump_json(indent=2))
    click.echo(f"Episode data: {episode_file}")

    stats_file = out_dir / "stats.json"
    stats_file.write_text(json.dumps(stats, indent=2))
    click.echo(f"Stats: {stats_file}")

    # Print summary
    click.echo(f"\n--- Results ---")
    click.echo(f"Games played: {stats['total_games']}")
    click.echo(f"Town wins: {stats['town_wins']} | Mafia wins: {stats['mafia_wins']}")
    click.echo(f"\nSuperlatives:")
    for title, name in stats["superlatives"].items():
        click.echo(f"  {title}: {name}")

    click.echo(f"\nPlayer stats:")
    for name, ps in stats["players"].items():
        click.echo(
            f"  {name}: {ps['win_rate']}% win rate | "
            f"Mafia WR: {ps['mafia_win_rate']}% | "
            f"Town WR: {ps['town_win_rate']}%"
        )


@cli.command()
@click.argument("result_file", type=click.Path(exists=True))
def show(result_file: str):
    """Show stats from a result file."""
    data = json.loads(Path(result_file).read_text())
    if "stats" in data:
        stats = data["stats"]
    else:
        click.echo("No stats found in file")
        return

    click.echo(f"Games: {stats['total_games']} | Town: {stats['town_wins']} | Mafia: {stats['mafia_wins']}")
    for name, ps in stats["players"].items():
        click.echo(f"  {name}: {ps['win_rate']}% WR")


if __name__ == "__main__":
    cli()
