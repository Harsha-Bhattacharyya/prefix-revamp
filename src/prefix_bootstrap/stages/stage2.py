"""
prefix_bootstrap.stages.stage2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stage 2 — Build the GNU toolchain.

Packages built in this stage (in dependency order):

  m4, autoconf, automake, libtool, pkg-config, binutils, gcc

Stage 2 uses the tools installed by Stage 1 (in ``$WORK_DIR/tools/bin``)
and installs its own outputs into ``$EPREFIX/usr``.

Like Stage 1, the stage is idempotent. :)
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

_STAGE = 2


def _sentinel(work_dir: Path, pkg_name: str) -> Path:
    return work_dir / "stamps" / f"stage2.{pkg_name}.done"


def run(config: BootstrapConfig) -> None:
    """Execute Stage 2.

    Parameters
    ----------
    config:
        Active bootstrap configuration.
    """
    console.rule(f"[bold magenta]Stage {_STAGE} — GNU Build Toolchain[/bold magenta]")

    packages = topological_order(STAGE_PACKAGES[_STAGE])
    pending = [p for p in packages if not _sentinel(config.work_dir, p.name).exists()]

    if not pending:
        console.print("[green]  Stage 2 already complete — nothing to do.  :)[/green]")
        return

    console.print(f"  Packages to build: {', '.join(p.name for p in pending)}")

    dl = Downloader(config)
    asyncio.run(dl.fetch_all(pending))

    builder = Builder(config)
    stamps_dir = config.work_dir / "stamps"
    stamps_dir.mkdir(parents=True, exist_ok=True)

    for pkg in pending:
        tarball = config.downloads_dir / pkg.tarball_name
        src_dir = extract(tarball, config.build_dir / pkg.name)
        builder.build(pkg, src_dir)
        _sentinel(config.work_dir, pkg.name).touch()

    console.print("[bold green]  Stage 2 complete!  :D[/bold green]")
    log.info("stage2.complete")
