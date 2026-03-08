"""Tests for the prefix_bootstrap.cli module (typer app)."""

from __future__ import annotations

from typer.testing import CliRunner

from prefix_bootstrap.cli import app

runner = CliRunner()


class TestCli:
    def test_version_command(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "prefix-bootstrap" in result.output

    def test_show_deps_all_stages(self) -> None:
        result = runner.invoke(app, ["show-deps"])
        assert result.exit_code == 0
        # Should mention known packages
        assert "bash" in result.output
        assert "gcc" in result.output

    def test_show_deps_single_stage(self) -> None:
        result = runner.invoke(app, ["show-deps", "--stages", "1"])
        assert result.exit_code == 0
        assert "bash" in result.output

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Bootstrap" in result.output or "bootstrap" in result.output

    def test_run_wrong_arch_exits_1(self, monkeypatch: object) -> None:
        import platform

        monkeypatch.setattr(platform, "machine", lambda: "x86_64")
        result = runner.invoke(app, ["run", "--prefix", "/tmp/test"])
        assert result.exit_code == 1

    def test_run_non_linux_exits_1(self, monkeypatch: object) -> None:
        import sys

        runner_local = CliRunner()
        monkeypatch.setattr(sys, "platform", "darwin")
        result = runner_local.invoke(app, ["run", "--prefix", "/tmp/test"])
        assert result.exit_code == 1
