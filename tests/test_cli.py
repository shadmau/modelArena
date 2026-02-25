"""Tests for CLI commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from engine.cli import cli


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ModelArena" in result.output

    def test_mafia_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mafia", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output

    def test_dry_run(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "mafia", "--dry-run", "--games", "2",
            "--episode-id", "test", "--output", str(tmp_path),
        ])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "RESULTS" in result.output

        # Check output files exist
        episode_file = tmp_path / "test" / "episode.json"
        assert episode_file.exists()
        data = json.loads(episode_file.read_text())
        assert data["episode_id"] == "test"
        assert len(data["games"]) == 2

        stats_file = tmp_path / "test" / "stats.json"
        assert stats_file.exists()
        stats = json.loads(stats_file.read_text())
        assert stats["total_games"] == 2

    def test_dry_run_writes_individual_games(self, tmp_path):
        runner = CliRunner()
        runner.invoke(cli, [
            "mafia", "--dry-run", "--games", "3",
            "--episode-id", "test", "--output", str(tmp_path),
        ])
        game_files = list((tmp_path / "test").glob("test-*.json"))
        assert len(game_files) == 3

    def test_sample_command(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "sample", "--games", "2", "--output", str(tmp_path / "sample"),
        ])
        assert result.exit_code == 0
        game_files = list((tmp_path / "sample").glob("sample-*.json"))
        assert len(game_files) == 2

    def test_show_command(self, tmp_path):
        # First generate data
        runner = CliRunner()
        runner.invoke(cli, [
            "mafia", "--dry-run", "--games", "2",
            "--episode-id", "test", "--output", str(tmp_path),
        ])

        # Then show it
        episode_file = tmp_path / "test" / "episode.json"
        result = runner.invoke(cli, ["show", str(episode_file)])
        assert result.exit_code == 0
        assert "RESULTS" in result.output
