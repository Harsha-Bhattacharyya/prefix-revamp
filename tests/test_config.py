"""Tests for prefix_bootstrap.config."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from prefix_bootstrap.config import SUPPORTED_ARCH, BootstrapConfig


def _cfg(**kw: object) -> BootstrapConfig:
    from pathlib import Path

    defaults = {
        "prefix": Path("/tmp/test-prefix"),
        "work_dir": Path("/tmp/test-work"),
    }
    defaults.update(kw)
    return BootstrapConfig(**defaults)  # type: ignore[arg-type]


class TestBootstrapConfig:
    def test_defaults_set(self) -> None:
        cfg = _cfg()
        assert cfg.arch == SUPPORTED_ARCH
        assert cfg.parallel_downloads == 4
        assert cfg.retries == 3
        assert cfg.stages == [1, 2, 3]

    def test_chost_derived(self) -> None:
        cfg = _cfg()
        assert cfg.chost == f"{SUPPORTED_ARCH}-unknown-linux-gnu"

    def test_explicit_chost_preserved(self) -> None:
        cfg = _cfg(chost="aarch64-gentoo-linux-gnu")
        assert cfg.chost == "aarch64-gentoo-linux-gnu"

    def test_unsupported_arch_raises(self) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            _cfg(arch="x86_64")

    def test_invalid_stage_raises(self) -> None:
        with pytest.raises(ValidationError, match="Unknown stage"):
            _cfg(stages=[0, 4])

    def test_stages_deduplicated_and_sorted(self) -> None:
        cfg = _cfg(stages=[3, 1, 1])
        assert cfg.stages == [1, 3]

    def test_config_is_frozen(self) -> None:
        cfg = _cfg()
        with pytest.raises(ValidationError):
            cfg.arch = "x86_64"  # type: ignore[misc]

    def test_derived_paths(self) -> None:
        from pathlib import Path

        cfg = _cfg(work_dir=Path("/work"))
        assert cfg.downloads_dir == Path("/work/distfiles")
        assert cfg.build_dir == Path("/work/build")
        assert cfg.tools_dir == Path("/work/tools")

    def test_parallel_downloads_bounds(self) -> None:
        with pytest.raises(ValidationError):
            _cfg(parallel_downloads=0)
        with pytest.raises(ValidationError):
            _cfg(parallel_downloads=33)

    def test_retries_bounds(self) -> None:
        with pytest.raises(ValidationError):
            _cfg(retries=-1)
        with pytest.raises(ValidationError):
            _cfg(retries=11)
