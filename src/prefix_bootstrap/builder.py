"""
prefix_bootstrap.builder
~~~~~~~~~~~~~~~~~~~~~~~~

Build orchestration layer — drives ``./configure``, ``make``, and
``make install`` for each source package using *plumbum*.

All commands are run in a controlled environment: only the minimal set of
environment variables needed for a reproducible build is exposed to
sub-processes.  The prefix ``$EPREFIX`` is injected into ``PATH`` so that
previously installed tools are found automatically.

Playful status messages keep the operator informed without being terse.  :)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import structlog
from plumbum import ProcessExecutionError, local  # type: ignore[import-untyped]
from rich.console import Console

from prefix_bootstrap.config import BootstrapConfig
from prefix_bootstrap.packages.base import Package

log = structlog.get_logger(__name__)
console = Console()


class BuildError(RuntimeError):
    """Raised when a package build step fails."""


class Builder:
    """Drives the configure / make / install cycle for a single package.

    Parameters
    ----------
    config:
        Active :class:`~prefix_bootstrap.config.BootstrapConfig`.
    """

    def __init__(self, config: BootstrapConfig) -> None:
        self._cfg = config

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build(self, pkg: Package, src_dir: Path) -> None:
        """Configure, compile, and install *pkg* from *src_dir*.

        Parameters
        ----------
        pkg:
            The package to build.
        src_dir:
            The unpacked source tree (output of
            :func:`~prefix_bootstrap.extractor.extract`).

        Raises
        ------
        BuildError
            If any build step exits with a non-zero status.
        """
        console.print(
            f"[bold cyan]  Building[/bold cyan] [green]{pkg.name}-{pkg.version}[/green] ... :D"
        )
        build_dir = self._cfg.build_dir / pkg.name
        build_dir.mkdir(parents=True, exist_ok=True)

        env = self._build_env(pkg)
        install_prefix = self._install_prefix(pkg)

        self._run_configure(pkg, src_dir, build_dir, install_prefix, env)
        self._run_make(build_dir, env)
        self._run_make_install(build_dir, env)

        console.print(
            f"[bold green]  Installed[/bold green] [green]{pkg.name}-{pkg.version}[/green]"
            f" -> {install_prefix}  :)"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_env(self, pkg: Package) -> dict[str, str]:
        """Return a minimal, reproducible build environment."""
        tools = self._cfg.tools_dir
        prefix_bin = self._cfg.prefix / "usr" / "bin"
        system_paths = [
            str(tools / "bin"),
            str(prefix_bin),
            "/usr/bin",
            "/bin",
        ]
        env: dict[str, str] = {
            "PATH": ":".join(system_paths),
            "HOME": str(Path.home()),
            "TERM": os.environ.get("TERM", "xterm"),
            "CHOST": self._cfg.chost,
            "CFLAGS": "-O2 -pipe",
            "CXXFLAGS": "-O2 -pipe",
            "LDFLAGS": "",
            "LANG": "C",
            "LC_ALL": "C",
        }
        env.update(pkg.env)
        return env

    def _install_prefix(self, pkg: Package) -> Path:
        """Determine the installation prefix for a package by stage."""
        if pkg.stage == 1:
            # Stage 1 tools land in a temporary directory so they don't
            # pollute the final prefix tree yet.
            return self._cfg.tools_dir
        return self._cfg.prefix / "usr"

    def _run_configure(
        self,
        pkg: Package,
        src_dir: Path,
        build_dir: Path,
        install_prefix: Path,
        env: dict[str, str],
    ) -> None:
        configure_script = src_dir / "configure"
        if not configure_script.exists():
            # Some packages (bzip2) use a plain Makefile — skip configure.
            log.info("builder.configure.skip", package=pkg.name, reason="no configure script")
            return

        args = [
            f"--prefix={install_prefix}",
            f"--host={self._cfg.chost}",
            f"--build={self._cfg.chost}",
            *pkg.configure_flags,
        ]

        log.info("builder.configure", package=pkg.name, args=args)
        try:
            with local.env(**env):
                local[str(configure_script)].run(
                    args,
                    cwd=str(build_dir),
                    retcode=0,
                )
        except ProcessExecutionError as exc:
            raise BuildError(f"./configure failed for {pkg.name}:\n{exc.stderr}") from exc

    def _run_make(self, build_dir: Path, env: dict[str, str]) -> None:
        j = max(1, os.cpu_count() or 1)
        log.info("builder.make", cwd=str(build_dir), jobs=j)
        try:
            with local.env(**env):
                local["make"][f"-j{j}"].run(cwd=str(build_dir), retcode=0)
        except ProcessExecutionError as exc:
            raise BuildError(f"make failed:\n{exc.stderr}") from exc

    def _run_make_install(self, build_dir: Path, env: dict[str, str]) -> None:
        log.info("builder.make_install", cwd=str(build_dir))
        try:
            with local.env(**env):
                local["make"]["install"].run(cwd=str(build_dir), retcode=0)
        except ProcessExecutionError as exc:
            raise BuildError(f"make install failed:\n{exc.stderr}") from exc


def which_or_raise(name: str, path: str | None = None) -> str:
    """Return the full path to *name* on PATH, or raise ``BuildError``.

    Parameters
    ----------
    name:
        Executable name.
    path:
        Optional colon-separated PATH override.

    Returns
    -------
    str
        Absolute path to the executable.
    """
    found = shutil.which(name, path=path)
    if found is None:
        raise BuildError(
            f"Required tool '{name}' not found on PATH.  Please install it and try again. :/"
        )
    return found
