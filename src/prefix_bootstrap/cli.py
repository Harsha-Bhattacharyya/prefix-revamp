"""
prefix_bootstrap.cli
~~~~~~~~~~~~~~~~~~~~~

Typer-based command-line interface.

Commands
--------
run         Full bootstrap (stages 1-3, or a subset with ``--stages``).
download    Download tarballs only (no building).
show-deps   Print the dependency tree and exit.
resolve     Query GNU mirrors for the latest package versions.
version     Print the tool version and exit.

Examples::

    # Full bootstrap to /usr/local/gentoo
    prefix-bootstrap run --prefix /usr/local/gentoo

    # Only stages 1 and 2, verbose
    prefix-bootstrap run --prefix /gentoo --stages 1 --stages 2 --log-level DEBUG

    # Download tarballs into a custom work dir
    prefix-bootstrap download --prefix /gentoo --work-dir /mnt/fast/bootstrap

    # Show what would be built
    prefix-bootstrap show-deps

    # Resolve latest GNU package URLs (requires internet)
    prefix-bootstrap resolve
"""

from __future__ import annotations

import asyncio
import platform
import sys
from pathlib import Path
from typing import Annotated

import structlog
import typer
from rich.console import Console
from rich.table import Table

from prefix_bootstrap.__version__ import __version__
from prefix_bootstrap.config import SUPPORTED_ARCH, BootstrapConfig
from prefix_bootstrap.graph import dependency_summary
from prefix_bootstrap.log import configure_logging
from prefix_bootstrap.packages.definitions import STAGE_PACKAGES

log = structlog.get_logger(__name__)
console = Console()

app = typer.Typer(
    name="prefix-bootstrap",
    help=(
        "Modular Gentoo Prefix bootstrap for Linux aarch64 (arm64).  "
        "See https://wiki.gentoo.org/wiki/Prefix/Bootstrap for background."
    ),
    add_completion=False,
)

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

_PrefixOpt = Annotated[
    Path,
    typer.Option("--prefix", "-p", help="Gentoo Prefix root ($EPREFIX)."),
]
_WorkDirOpt = Annotated[
    Path | None,
    typer.Option("--work-dir", "-w", help="Scratch / build directory."),
]
_LogLevelOpt = Annotated[
    str,
    typer.Option("--log-level", help="Logging verbosity (DEBUG/INFO/WARNING/ERROR)."),
]
_JsonLogsOpt = Annotated[
    bool,
    typer.Option("--json-logs", help="Emit newline-delimited JSON log lines."),
]
_SkipVerifyOpt = Annotated[
    bool,
    typer.Option("--skip-verify", help="Skip checksum verification (not recommended)."),
]
_StagesOpt = Annotated[
    list[int] | None,
    typer.Option("--stages", "-s", help="Bootstrap stages to execute (1, 2, or 3)."),
]
_MirrorOpt = Annotated[
    str,
    typer.Option("--mirror", help="GNU FTP mirror base URL."),
]


def _make_config(
    prefix: Path,
    work_dir: Path | None,
    log_level: str,
    json_logs: bool,
    skip_verify: bool,
    stages: list[int] | None,
    mirror: str,
) -> BootstrapConfig:
    configure_logging(log_level, json_output=json_logs)
    wd = work_dir or (prefix / ".bootstrap-work")
    return BootstrapConfig(  # type: ignore[call-arg]
        prefix=prefix,
        work_dir=wd,
        log_level=log_level,
        json_logs=json_logs,
        skip_verify=skip_verify,
        stages=stages or [1, 2, 3],
        gnu_mirror=mirror,
    )


def _check_platform() -> None:
    """Abort early on unsupported platforms."""
    machine = platform.machine().lower()
    if machine not in ("aarch64", "arm64"):
        console.print(
            f"[bold red]ERROR:[/bold red] Unsupported architecture '{machine}'.  "
            f"Only {SUPPORTED_ARCH} (arm64) is supported.  :/"
        )
        raise typer.Exit(code=1)
    if sys.platform != "linux":
        console.print("[bold red]ERROR:[/bold red] Only Linux is supported.  :/")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def run(
    prefix: _PrefixOpt = Path("/usr/local/gentoo"),
    work_dir: _WorkDirOpt = None,
    log_level: _LogLevelOpt = "INFO",
    json_logs: _JsonLogsOpt = False,
    skip_verify: _SkipVerifyOpt = False,
    stages: _StagesOpt = None,
    mirror: _MirrorOpt = "https://ftpmirror.gnu.org",
) -> None:
    """Run the full Gentoo Prefix bootstrap (all stages, or a subset).

    This command downloads, compiles, and installs every required package
    in the correct dependency order.  It is safe to re-run — completed
    packages are detected via stamp files and skipped. :)
    """
    _check_platform()
    cfg = _make_config(prefix, work_dir, log_level, json_logs, skip_verify, stages, mirror)

    console.print(
        f"[bold]prefix-bootstrap[/bold] v{__version__}  —  "
        f"prefix=[green]{prefix}[/green]  stages={cfg.stages}  :D"
    )

    from prefix_bootstrap.stages import stage1, stage2, stage3

    stage_runners = {1: stage1.run, 2: stage2.run, 3: stage3.run}
    for stage_num in cfg.stages:
        stage_runners[stage_num](cfg)

    console.print("\n[bold green]Bootstrap complete!  Happy Gentooing!  :D[/bold green]")


@app.command()
def download(
    prefix: _PrefixOpt = Path("/usr/local/gentoo"),
    work_dir: _WorkDirOpt = None,
    log_level: _LogLevelOpt = "INFO",
    json_logs: _JsonLogsOpt = False,
    skip_verify: _SkipVerifyOpt = False,
    stages: _StagesOpt = None,
    mirror: _MirrorOpt = "https://ftpmirror.gnu.org",
) -> None:
    """Download tarballs for all (or selected) stages without building.

    Useful for pre-fetching in a networked environment before doing the
    actual build in an offline or rate-limited environment.
    """
    _check_platform()
    cfg = _make_config(prefix, work_dir, log_level, json_logs, skip_verify, stages, mirror)

    from prefix_bootstrap.downloader import Downloader
    from prefix_bootstrap.graph import topological_order

    stage_nums = cfg.stages
    pkgs = []
    for s in stage_nums:
        pkgs.extend(topological_order(STAGE_PACKAGES[s]))

    console.print(f"  Downloading {len(pkgs)} packages for stages {stage_nums} ...")
    dl = Downloader(cfg)
    asyncio.run(dl.fetch_all(pkgs))
    console.print("[bold green]  All downloads complete.  :)[/bold green]")


@app.command(name="show-deps")
def show_deps(
    stages: _StagesOpt = None,
) -> None:
    """Print the dependency tree for all (or selected) stages and exit.

    No network access or root privileges required.
    """
    from prefix_bootstrap.graph import topological_order

    stage_nums = stages or [1, 2, 3]
    pkgs = []
    for s in stage_nums:
        pkgs.extend(topological_order(STAGE_PACKAGES[s]))

    console.print(f"\n[bold]Build order for stages {stage_nums}:[/bold]")
    console.print(dependency_summary(pkgs))


@app.command()
def resolve(
    mirror: _MirrorOpt = "https://ftpmirror.gnu.org",
    log_level: _LogLevelOpt = "INFO",
    json_logs: _JsonLogsOpt = False,
) -> None:
    """Query GNU mirrors and print the latest version of each GNU package.

    Requires internet access.  Non-GNU packages (openssl, curl, rsync,
    pkg-config, xz, zlib, bzip2) are reported with their catalogue version.
    """
    configure_logging(log_level, json_output=json_logs)

    gnu_projects = [
        "bash",
        "coreutils",
        "findutils",
        "grep",
        "sed",
        "gawk",
        "make",
        "patch",
        "tar",
        "m4",
        "autoconf",
        "automake",
        "libtool",
        "binutils",
    ]

    from prefix_bootstrap.packages.gnu import resolve_all_latest

    console.print("[bold]Resolving latest GNU package versions ...[/bold]")
    results = asyncio.run(resolve_all_latest(gnu_projects, mirror=mirror))

    table = Table(title="Latest GNU Packages", show_header=True)
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("URL")

    for name in gnu_projects:
        if name in results:
            url, ver = results[name]
            table.add_row(name, ver, url)
        else:
            table.add_row(name, "(failed)", "")

    console.print(table)


@app.command()
def version() -> None:
    """Print the prefix-bootstrap version and exit."""
    console.print(f"prefix-bootstrap {__version__}")
