"""CLI to run ModelArena games."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

from engine.games.mafia import run_episode
from engine.models import EpisodeResult
from engine.players.llm_player import LLMPlayer, get_default_players
from engine.players.mock_player import MockLLMPlayer
from engine.stats import compute_episode_stats


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool):
    """ModelArena — LLMs compete in games."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@cli.command()
@click.option("--games", "-n", default=10, help="Number of games to run")
@click.option("--episode-id", "-e", default="ep001", help="Episode ID")
@click.option("--output", "-o", default="results", help="Output directory")
@click.option("--dry-run", is_flag=True, help="Run with mock players (no API keys needed)")
def mafia(games: int, episode_id: str, output: str, dry_run: bool):
    """Run a Mafia episode."""
    mode = "DRY RUN (mock)" if dry_run else "LIVE"
    click.echo(f"Running Mafia episode: {episode_id} ({games} games) [{mode}]")

    player_infos = get_default_players()
    if dry_run:
        players = [MockLLMPlayer(p) for p in player_infos]
    else:
        players = [LLMPlayer(p) for p in player_infos]

    results = run_episode(players, num_games=games, episode_id=episode_id)
    stats = compute_episode_stats(results)

    episode = EpisodeResult(
        episode_id=episode_id,
        episode_title=f"Mafia — Episode {episode_id}",
        games=results,
        stats=stats,
    )

    out_dir = Path(output) / episode_id
    out_dir.mkdir(parents=True, exist_ok=True)

    episode_file = out_dir / "episode.json"
    episode_file.write_text(episode.model_dump_json(indent=2))
    click.echo(f"Wrote: {episode_file}")

    stats_file = out_dir / "stats.json"
    stats_file.write_text(json.dumps(stats, indent=2))
    click.echo(f"Wrote: {stats_file}")

    # Also write individual game files for the video pipeline
    for game_result in results:
        game_file = out_dir / f"{game_result.game_id}.json"
        game_file.write_text(game_result.model_dump_json(indent=2))

    click.echo(f"Wrote {len(results)} individual game files")

    _print_summary(stats, dry_run)

    if not dry_run:
        _print_costs(players)


@cli.command()
@click.argument("result_file", type=click.Path(exists=True))
def show(result_file: str):
    """Show stats from a result file."""
    data = json.loads(Path(result_file).read_text())
    if "stats" in data:
        _print_summary(data["stats"])
    else:
        click.echo("No stats found in file")


@cli.command(name="sample")
@click.option("--games", "-n", default=5, help="Number of games to generate")
@click.option("--output", "-o", default="results/sample", help="Output directory")
def generate_sample(games: int, output: str):
    """Generate sample game data using mock players (for video pipeline testing)."""
    click.echo(f"Generating {games} sample games...")

    player_infos = get_default_players()
    players = [MockLLMPlayer(p) for p in player_infos]

    results = run_episode(players, num_games=games, episode_id="sample")
    stats = compute_episode_stats(results)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write individual games (what the video pipeline consumes)
    for game_result in results:
        game_file = out_dir / f"{game_result.game_id}.json"
        game_file.write_text(game_result.model_dump_json(indent=2))

    stats_file = out_dir / "stats.json"
    stats_file.write_text(json.dumps(stats, indent=2))

    click.echo(f"Wrote {len(results)} game files + stats to {out_dir}/")
    _print_summary(stats)


def _print_summary(stats: dict, dry_run: bool = False):
    click.echo(f"\n{'═' * 50}")
    click.echo(f"  RESULTS — {stats['total_games']} games")
    click.echo(f"  Town: {stats['town_wins']}W | Mafia: {stats['mafia_wins']}W")
    click.echo(f"{'═' * 50}")

    click.echo(f"\n  {'Player':<12} {'WR':>6} {'Mafia':>7} {'Town':>7} {'Detect':>7}")
    click.echo(f"  {'─' * 42}")
    for name, ps in stats["players"].items():
        click.echo(
            f"  {name:<12} {ps['win_rate']:>5.1f}% "
            f"{ps['mafia_win_rate']:>5.1f}% "
            f"{ps['town_win_rate']:>5.1f}% "
            f"{ps['detection_rate']:>5.1f}%"
        )

    click.echo("\n  Awards:")
    for title, name in stats["superlatives"].items():
        label = title.replace("_", " ").title()
        click.echo(f"    {label}: {name}")
    click.echo()


def _print_costs(players: list):
    total_prompt = sum(p.stats.total_prompt_tokens for p in players if hasattr(p, "stats"))
    total_completion = sum(p.stats.total_completion_tokens for p in players if hasattr(p, "stats"))
    total_calls = sum(p.stats.total_calls for p in players if hasattr(p, "stats"))
    total_retries = sum(p.stats.retries for p in players if hasattr(p, "stats"))

    if total_calls > 0:
        click.echo("  API Usage:")
        click.echo(f"    Calls: {total_calls} (retries: {total_retries})")
        click.echo(f"    Tokens: {total_prompt:,} prompt + {total_completion:,} completion")


if __name__ == "__main__":
    cli()
