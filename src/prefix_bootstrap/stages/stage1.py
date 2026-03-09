"""
prefix_bootstrap.stages.stage1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stage 1 — Bootstrap essential GNU userland tools.

Packages built in this stage (in dependency order):

  zlib, bzip2, xz, bash, coreutils, findutils, grep, sed, gawk, make,
  patch, tar

These are compiled with the *system* compiler and installed into
``$WORK_DIR/tools`` so they are available for Stage 2 without touching
the final prefix tree yet.

The stage is idempotent: already-built packages are detected via a
sentinel file and skipped with a cheerful message. :)
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog
from rich.console import Console

from prefix_bootstrap.builder import Builder
from prefix_bootstrap.config import BootstrapConfig
from prefix_bootstrap.downloader import Downloader
from prefix_bootstrap.extractor import extract
from prefix_bootstrap.graph import topological_order
from prefix_bootstrap.packages.definitions import STAGE_PACKAGES

log = structlog.get_logger(__name__)
console = Console()

_STAGE = 1


def _sentinel(work_dir: Path, pkg_name: str) -> Path:
    return work_dir / "stamps" / f"stage1.{pkg_name}.done"


def run(config: BootstrapConfig) -> None:
    """Execute Stage 1.

    Downloads all Stage-1 tarballs in parallel, then builds and installs
    each package in topological order.

    Parameters
    ----------
    config:
        Active bootstrap configuration.
    """
    console.rule(f"[bold magenta]Stage {_STAGE} — Essential GNU Tools[/bold magenta]")

    packages = topological_order(STAGE_PACKAGES[_STAGE])
    pending = [p for p in packages if not _sentinel(config.work_dir, p.name).exists()]

    if not pending:
        console.print("[green]  Stage 1 already complete — nothing to do.  :)[/green]")
        return

    console.print(f"  Packages to build: {', '.join(p.name for p in pending)}")

    # Download phase
    dl = Downloader(config)
    asyncio.run(dl.fetch_all(pending))

    # Build phase
    builder = Builder(config)
    stamps_dir = config.work_dir / "stamps"
    stamps_dir.mkdir(parents=True, exist_ok=True)

    for pkg in pending:
        tarball = config.downloads_dir / pkg.tarball_name
        src_dir = extract(tarball, config.build_dir / pkg.name)
        builder.build(pkg, src_dir)

        # Write sentinel
        _sentinel(config.work_dir, pkg.name).touch()

    console.print("[bold green]  Stage 1 complete!  :D[/bold green]")
    log.info("stage1.complete")
