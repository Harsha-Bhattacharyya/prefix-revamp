"""
Tests for prefix_bootstrap.tui — the Textual interactive UI.

We only test the non-UI components (ASCII art, welcome text, env var
checking) since full Textual rendering requires a terminal.
"""

from __future__ import annotations

from prefix_bootstrap.tui import (
    _CHECKED_ENV_VARS,
    GENTOO_BANNER,
    WELCOME_TEXT,
)


class TestBanner:
    """The ASCII art banner must be preserved verbatim from the original script."""

    def test_banner_not_empty(self) -> None:
        assert GENTOO_BANNER.strip()

    def test_banner_contains_dollar_signs(self) -> None:
        # The original Gentoo diamond logo uses $-characters.
        assert "$" in GENTOO_BANNER

    def test_banner_contains_vir(self) -> None:
        # ".vir." is the tip of the original ASCII art.
        assert ".vir." in GENTOO_BANNER

    def test_banner_multiline(self) -> None:
        assert GENTOO_BANNER.count("\n") >= 8


class TestWelcomeText:
    def test_welcome_mentions_gentoo(self) -> None:
        assert "Gentoo" in WELCOME_TEXT

    def test_welcome_not_empty(self) -> None:
        assert len(WELCOME_TEXT) > 50


class TestCheckedEnvVars:
    def test_checked_vars_includes_expected(self) -> None:
        # These are the vars the original script rejects.
        for var in ("LD_LIBRARY_PATH", "PKG_CONFIG_PATH", "PYTHONPATH", "CFLAGS"):
            assert var in _CHECKED_ENV_VARS

    def test_checked_vars_non_empty(self) -> None:
        assert len(_CHECKED_ENV_VARS) >= 10


class TestTUIImport:
    """Verify TUI components can be imported without a running terminal."""

    def test_run_tui_importable(self) -> None:
        from prefix_bootstrap.tui import run_tui  # noqa: F401

    def test_bootstrap_tui_importable(self) -> None:
        from prefix_bootstrap.tui import BootstrapTUI  # noqa: F401

    def test_stage_progress_importable(self) -> None:
        from prefix_bootstrap.tui import StageProgress  # noqa: F401
