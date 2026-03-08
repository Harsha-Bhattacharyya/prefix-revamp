"""
Tests for prefix_bootstrap.bootstrap — the core bootstrap orchestration
module that mirrors the original bootstrap-prefix.sh function naming.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from prefix_bootstrap.bootstrap import (
    _already_done,
    _mark_done,
    _stamp,
    bootstrap_bash,
    bootstrap_bison,
    bootstrap_bzip2,
    bootstrap_coreutils,
    bootstrap_findutils,
    bootstrap_gawk,
    bootstrap_grep,
    bootstrap_gzip,
    bootstrap_libffi,
    bootstrap_libressl,
    bootstrap_m4,
    bootstrap_make,
    bootstrap_patch,
    bootstrap_sed,
    bootstrap_tar,
    bootstrap_wget,
    bootstrap_xz,
    bootstrap_zlib,
    eerror,
    einfo,
    estatus,
)
from prefix_bootstrap.config import BootstrapConfig


def _config(tmp_path: Path) -> BootstrapConfig:
    return BootstrapConfig(  # type: ignore[call-arg]
        prefix=tmp_path / "prefix",
        work_dir=tmp_path / "work",
    )


class TestOutputHelpers:
    """Tests for einfo / eerror / estatus — the original-style output helpers."""

    def test_einfo_runs_without_error(self, capsys: Any) -> None:
        einfo("Hello, Gentoo!  :D")
        # Rich Console writes to stdout; just verify no exception raised.

    def test_eerror_runs_without_error(self, capsys: Any) -> None:
        eerror("Something went wrong  :/")

    def test_estatus_non_tty(self) -> None:
        # In a non-TTY environment estatus should be a no-op.
        estatus("stage1: building bash-5.3")


class TestStampFiles:
    """Tests for stamp-file idempotency helpers."""

    def test_stamp_path(self, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        path = _stamp(cfg, "bash")
        assert path.parent.name == "stamps"
        assert path.name == "bash.done"

    def test_not_done_initially(self, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        assert _already_done(cfg, "bash") is False

    def test_mark_done_creates_stamp(self, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        _mark_done(cfg, "bash")
        assert _already_done(cfg, "bash") is True

    def test_mark_done_idempotent(self, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        _mark_done(cfg, "bash")
        _mark_done(cfg, "bash")  # should not raise
        assert _already_done(cfg, "bash") is True


class TestSkipIfDoneDecorator:
    """The @_skip_if_done decorator skips bootstrappers when stamp exists."""

    def test_skips_when_stamp_present(self, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        _mark_done(cfg, "make")
        called = [False]

        def _track(c: BootstrapConfig) -> None:
            called[0] = True

        with patch("prefix_bootstrap.bootstrap.bootstrap_gnu", side_effect=_track):
            bootstrap_make(cfg)

        assert not called[0], "bootstrap_gnu should not be called when stamp exists"

    def test_runs_when_stamp_absent(self, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        # Patch bootstrap_gnu to avoid actual network/build activity.
        with patch("prefix_bootstrap.bootstrap.bootstrap_gnu") as mock_gnu:
            bootstrap_make(cfg)
            mock_gnu.assert_called_once()
        # Stamp should now exist.
        assert _already_done(cfg, "make")


class TestPerPackageBootstrappers:
    """Smoke-test that all per-package bootstrappers delegate correctly."""

    # Packages that ultimately call bootstrap_simple
    _SIMPLE_PKGS = [bootstrap_bzip2, bootstrap_libressl, bootstrap_zlib]

    # Packages that ultimately call bootstrap_gnu
    _GNU_PKGS = [
        bootstrap_xz,
        bootstrap_gzip,
        bootstrap_make,
        bootstrap_wget,
        bootstrap_sed,
        bootstrap_patch,
        bootstrap_m4,
        bootstrap_bison,
        bootstrap_grep,
        bootstrap_coreutils,
        bootstrap_findutils,
        bootstrap_gawk,
        bootstrap_tar,
        bootstrap_bash,
        bootstrap_libffi,
    ]

    @pytest.mark.parametrize("fn", _GNU_PKGS)
    def test_gnu_pkg_calls_bootstrap_gnu(self, fn: Any, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        with patch("prefix_bootstrap.bootstrap.bootstrap_gnu") as mock_gnu:
            fn(cfg)
            mock_gnu.assert_called_once()

    @pytest.mark.parametrize("fn", _SIMPLE_PKGS)
    def test_simple_pkg_calls_bootstrap_simple(self, fn: Any, tmp_path: Path) -> None:
        cfg = _config(tmp_path)
        with patch("prefix_bootstrap.bootstrap.bootstrap_simple") as mock_simple:
            fn(cfg)
            mock_simple.assert_called_once()
