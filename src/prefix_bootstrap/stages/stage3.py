"""
prefix_bootstrap.stages.stage3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Stage 3 — Build Portage prerequisites.

Packages built in this stage (in dependency order):

  openssl, curl, rsync

After Stage 3 the prefix has all the networking tools needed to run
``emerge`` and bootstrap Portage itself.  :)
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

_STAGE = 3


def _sentinel(work_dir: Path, pkg_name: str) -> Path:
    return work_dir / "stamps" / f"stage3.{pkg_name}.done"


def run(config: BootstrapConfig) -> None:
    """Execute Stage 3.

    Parameters
    ----------
    config:
        Active bootstrap configuration.
    """
    console.rule(f"[bold magenta]Stage {_STAGE} — Portage Prerequisites[/bold magenta]")

    packages = topological_order(STAGE_PACKAGES[_STAGE])
    pending = [p for p in packages if not _sentinel(config.work_dir, p.name).exists()]

    if not pending:
        console.print("[green]  Stage 3 already complete — nothing to do.  :)[/green]")
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

    console.print("[bold green]  Stage 3 complete!  Portage is ready.  :D[/bold green]")
    log.info("stage3.complete")
