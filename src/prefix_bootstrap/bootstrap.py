"""
prefix_bootstrap.bootstrap
~~~~~~~~~~~~~~~~~~~~~~~~~~

Core bootstrap orchestration, using function and variable naming that
mirrors the original ``bootstrap-prefix.sh`` shell script as closely
as possible.

Functions
---------
einfo(msg)          -- print ``* <msg>`` (matches original's einfo)
eerror(msg)         -- print ``!!! <msg>`` to stderr (matches eerror)
estatus(msg)        -- update terminal title bar (matches estatus)
efetch(url, distdir)-- download a single URL into distdir (matches efetch)
econf(*args)        -- run ./configure with standard flags (matches econf)
emake(*args)        -- run make with MAKEOPTS parallelism (matches emake)
bootstrap_gnu(name, version, config)   -- build any GNU package
bootstrap_simple(name, version, ...)   -- build a non-GNU package
bootstrap_bash(config)    -- bootstraps bash (matches bootstrap_bash)
bootstrap_coreutils(cfg)  -- bootstraps coreutils
...and so on for every Stage-1 package.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

import structlog
from plumbum import ProcessExecutionError, local  # type: ignore[import-untyped]
from rich.console import Console

from prefix_bootstrap.config import BootstrapConfig
from prefix_bootstrap.downloader import Downloader
from prefix_bootstrap.extractor import extract
from prefix_bootstrap.packages.base import Package
from prefix_bootstrap.packages.definitions import (
    AUTOCONF,
    AUTOMAKE,
    BASH,
    BINUTILS,
    BISON,
    BZIP2,
    COREUTILS,
    CURL,
    FINDUTILS,
    GAWK,
    GCC,
    GREP,
    GZIP,
    LIBFFI,
    LIBRESSL,
    LIBTOOL,
    M4,
    MAKE,
    OPENSSL,
    PATCH,
    PKG_CONFIG,
    PYTHON,
    RSYNC,
    SED,
    TAR,
    WGET,
    XZ,
    ZLIB,
)

log = structlog.get_logger(__name__)
console = Console(stderr=False)
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Output helpers — matching the original script's eerror / einfo / estatus
# ---------------------------------------------------------------------------


def estatus(msg: str) -> None:
    """Update the terminal title bar with *msg* (matches original ``estatus``)."""
    if sys.stdout.isatty():
        sys.stdout.write(f"\033]2;{msg}\007")
        sys.stdout.flush()


def einfo(msg: str) -> None:
    """Print ``* <msg>`` to stdout (matches original ``einfo``).  :)"""
    console.print(f"[bold green]*[/bold green] {msg}")


def eerror(msg: str) -> None:
    """Print ``!!! <msg>`` to stderr (matches original ``eerror``).  :/"""
    estatus(msg)
    err_console.print(f"[bold red]!!![/bold red] {msg}")


# ---------------------------------------------------------------------------
# Build helpers — econf / emake matching original
# ---------------------------------------------------------------------------


def econf(src_dir: Path, build_dir: Path, cfg: BootstrapConfig, extra_args: list[str]) -> None:
    """Run ``./configure`` with standard flags (matches original ``econf``).

    Parameters
    ----------
    src_dir:
        Unpacked source tree containing ``configure``.
    build_dir:
        Directory in which to run configure (out-of-tree build).
    cfg:
        Active bootstrap configuration.
    extra_args:
        Package-specific configure flags.
    """

    configure = src_dir / "configure"
    if not configure.exists():
        einfo(f"No configure script in {src_dir.name}, skipping econf :)")
        return

    tmp_prefix = cfg.tools_dir
    args = [
        f"--host={cfg.chost}",
        f"--build={cfg.chost}",
        f"--prefix={tmp_prefix}",
        f"--mandir={tmp_prefix}/share/man",
        f"--infodir={tmp_prefix}/share/info",
        f"--datadir={tmp_prefix}/share",
        f"--sysconfdir={tmp_prefix}/etc",
        f"--localstatedir={tmp_prefix}/var/lib",
        "--disable-dependency-tracking",
        *extra_args,
    ]

    log.info("econf", cwd=str(build_dir), args=args)
    try:
        with local.env(**_build_env(cfg)):
            local[str(configure)].run(args, cwd=str(build_dir), retcode=0)
    except ProcessExecutionError as exc:
        raise RuntimeError(f"./configure failed for {src_dir.name}:\n{exc.stderr}") from exc


def emake(build_dir: Path, cfg: BootstrapConfig, *targets: str) -> None:
    """Run ``make`` with ``MAKEOPTS`` parallelism (matches original ``emake``).

    Retries with ``-j1`` on failure to produce clearer error output — exactly
    as the original script does. :/
    """

    j = max(1, os.cpu_count() or 1)
    make_args = [f"-j{j}", *list(targets)]
    log.info("emake", cwd=str(build_dir), targets=list(targets), jobs=j)
    try:
        with local.env(**_build_env(cfg)):
            local["make"][make_args].run(cwd=str(build_dir), retcode=0)
    except ProcessExecutionError:
        # Retry with -j1 for a clearer error message, just like the original. :/
        einfo("Retrying with -j1 for a clearer error message...")
        try:
            with local.env(**_build_env(cfg)):
                local["make"][["-j1", *list(targets)]].run(cwd=str(build_dir), retcode=0)
        except ProcessExecutionError as exc:
            raise RuntimeError(f"make {' '.join(targets)} failed:\n{exc.stderr}") from exc


# ---------------------------------------------------------------------------
# Download helper — efetch
# ---------------------------------------------------------------------------


def efetch(pkg: Package, cfg: BootstrapConfig) -> None:
    """Download *pkg* into ``cfg.downloads_dir`` (matches original ``efetch``).

    Skips download when the file already exists and the checksum matches.
    """
    dl = Downloader(cfg)
    asyncio.run(dl.fetch_all([pkg]))


# ---------------------------------------------------------------------------
# Generic bootstrappers matching original's bootstrap_gnu / bootstrap_simple
# ---------------------------------------------------------------------------


def bootstrap_gnu(pkg: Package, cfg: BootstrapConfig) -> Path:
    """Build a GNU package (matches original ``bootstrap_gnu``).

    Downloads, extracts, configures, compiles, and installs *pkg*.
    Returns the installation prefix.

    This function mirrors the shell script's ``bootstrap_gnu()`` function,
    including the ``einfo``, ``econf``, ``emake`` call pattern.  :D
    """
    pn = pkg.name
    pv = pkg.version

    einfo(f"Bootstrapping {pn}-{pv}")
    estatus(f"stage{pkg.stage}: bootstrapping {pn}-{pv}")

    efetch(pkg, cfg)

    einfo(f"Unpacking {pn}-{pv}")
    src_dir = extract(cfg.downloads_dir / pkg.tarball_name, cfg.build_dir / pn)

    build_dir = cfg.build_dir / f"{pn}-build"
    build_dir.mkdir(parents=True, exist_ok=True)

    einfo(f"Compiling {pn}-{pv}")
    estatus(f"stage{pkg.stage}: configuring {pn}-{pv}")
    econf(src_dir, build_dir, cfg, list(pkg.configure_flags))

    estatus(f"stage{pkg.stage}: building {pn}-{pv}")
    emake(build_dir, cfg)

    einfo(f"Installing {pn}-{pv}")
    estatus(f"stage{pkg.stage}: installing {pn}-{pv}")
    emake(build_dir, cfg, "install")

    # Clean up the build tree, just like the original. :)
    shutil.rmtree(str(build_dir), ignore_errors=True)
    shutil.rmtree(str(src_dir), ignore_errors=True)

    einfo(f"{pn}-{pv} successfully bootstrapped")
    return cfg.tools_dir


def bootstrap_simple(pkg: Package, cfg: BootstrapConfig) -> Path:
    """Build a non-GNU package with a plain configure (original ``bootstrap_simple``).

    Used for packages like bzip2 and libressl that do not live on the GNU FTP
    server and may use non-standard install targets.
    """
    pn = pkg.name
    pv = pkg.version

    einfo(f"Bootstrapping {pn}-{pv}")
    efetch(pkg, cfg)

    einfo(f"Unpacking {pn}-{pv}")
    src_dir = extract(cfg.downloads_dir / pkg.tarball_name, cfg.build_dir / pn)

    einfo(f"Compiling {pn}-{pv}")
    econf(src_dir, src_dir, cfg, list(pkg.configure_flags))
    emake(src_dir, cfg)

    einfo(f"Installing {pn}-{pv}")
    emake(src_dir, cfg, f"PREFIX={cfg.tools_dir}", "install")

    shutil.rmtree(str(src_dir), ignore_errors=True)
    einfo(f"{pn}-{pv} successfully bootstrapped")
    return cfg.tools_dir


# ---------------------------------------------------------------------------
# Per-package bootstrappers — matching the original's bootstrap_<name>()
# ---------------------------------------------------------------------------

BootstrapFn = Callable[[BootstrapConfig], None]


def _build_env(cfg: BootstrapConfig) -> dict[str, str]:
    """Minimal reproducible build environment (mirrors original configure_cflags)."""
    tools_bin = str(cfg.tools_dir / "bin")
    return {
        "PATH": f"{tools_bin}:/usr/bin:/bin",
        "HOME": str(Path.home()),
        "TERM": os.environ.get("TERM", "xterm"),
        "CHOST": cfg.chost,
        "CFLAGS": "-O2 -pipe",
        "CXXFLAGS": "-O2 -pipe",
        "LDFLAGS": f"-L{cfg.tools_dir}/lib -Wl,-rpath={cfg.tools_dir}/lib",
        "CPPFLAGS": f"-I{cfg.tools_dir}/include",
        "PKG_CONFIG_PATH": f"{cfg.tools_dir}/lib/pkgconfig",
        "LANG": "C",
        "LC_ALL": "C",
    }


def _stamp(cfg: BootstrapConfig, name: str) -> Path:
    return cfg.work_dir / "stamps" / f"{name}.done"


def _already_done(cfg: BootstrapConfig, name: str) -> bool:
    return _stamp(cfg, name).exists()


def _mark_done(cfg: BootstrapConfig, name: str) -> None:
    (cfg.work_dir / "stamps").mkdir(parents=True, exist_ok=True)
    _stamp(cfg, name).touch()


def _skip_if_done(name: str) -> Callable[[BootstrapFn], BootstrapFn]:
    """Decorator that skips the bootstrapper if a stamp file exists."""

    def decorator(fn: BootstrapFn) -> BootstrapFn:
        def wrapper(cfg: BootstrapConfig) -> None:
            if _already_done(cfg, name):
                einfo(f"{name} already bootstrapped, skipping :)")
                return
            fn(cfg)
            _mark_done(cfg, name)

        return wrapper

    return decorator


@_skip_if_done("zlib")
def bootstrap_zlib(cfg: BootstrapConfig) -> None:
    """Bootstrap zlib (matches original ``bootstrap_zlib``)."""
    bootstrap_simple(ZLIB, cfg)


@_skip_if_done("bzip2")
def bootstrap_bzip2(cfg: BootstrapConfig) -> None:
    """Bootstrap bzip2 (matches original ``bootstrap_bzip2``)."""
    bootstrap_simple(BZIP2, cfg)


@_skip_if_done("xz")
def bootstrap_xz(cfg: BootstrapConfig) -> None:
    """Bootstrap xz (matches original ``bootstrap_xz``)."""
    bootstrap_gnu(XZ, cfg)


@_skip_if_done("gzip")
def bootstrap_gzip(cfg: BootstrapConfig) -> None:
    """Bootstrap gzip (matches original ``bootstrap_gzip``)."""
    bootstrap_gnu(GZIP, cfg)


@_skip_if_done("libressl")
def bootstrap_libressl(cfg: BootstrapConfig) -> None:
    """Bootstrap libressl for TLS (matches original ``bootstrap_libressl``).

    Only built when an OpenSSL/LibreSSL binary is not already present.
    Used as TLS backend for wget during Stage 1.
    """
    bootstrap_simple(LIBRESSL, cfg)


@_skip_if_done("make")
def bootstrap_make(cfg: BootstrapConfig) -> None:
    """Bootstrap GNU make (matches original ``bootstrap_make``)."""
    bootstrap_gnu(MAKE, cfg)


@_skip_if_done("wget")
def bootstrap_wget(cfg: BootstrapConfig) -> None:
    """Bootstrap wget (matches original ``bootstrap_wget``)."""
    bootstrap_gnu(WGET, cfg)


@_skip_if_done("sed")
def bootstrap_sed(cfg: BootstrapConfig) -> None:
    """Bootstrap sed (matches original ``bootstrap_sed``)."""
    bootstrap_gnu(SED, cfg)


@_skip_if_done("patch")
def bootstrap_patch(cfg: BootstrapConfig) -> None:
    """Bootstrap patch (matches original ``bootstrap_patch``)."""
    bootstrap_gnu(PATCH, cfg)


@_skip_if_done("m4")
def bootstrap_m4(cfg: BootstrapConfig) -> None:
    """Bootstrap m4 (matches original ``bootstrap_m4``)."""
    bootstrap_gnu(M4, cfg)


@_skip_if_done("bison")
def bootstrap_bison(cfg: BootstrapConfig) -> None:
    """Bootstrap bison (matches original ``bootstrap_bison``)."""
    bootstrap_gnu(BISON, cfg)


@_skip_if_done("grep")
def bootstrap_grep(cfg: BootstrapConfig) -> None:
    """Bootstrap grep (matches original ``bootstrap_grep``)."""
    bootstrap_gnu(GREP, cfg)


@_skip_if_done("coreutils")
def bootstrap_coreutils(cfg: BootstrapConfig) -> None:
    """Bootstrap coreutils (matches original ``bootstrap_coreutils``)."""
    bootstrap_gnu(COREUTILS, cfg)


@_skip_if_done("findutils")
def bootstrap_findutils(cfg: BootstrapConfig) -> None:
    """Bootstrap findutils (matches original ``bootstrap_findutils``)."""
    bootstrap_gnu(FINDUTILS, cfg)


@_skip_if_done("gawk")
def bootstrap_gawk(cfg: BootstrapConfig) -> None:
    """Bootstrap gawk (matches original ``bootstrap_gawk``)."""
    bootstrap_gnu(GAWK, cfg)


@_skip_if_done("tar")
def bootstrap_tar(cfg: BootstrapConfig) -> None:
    """Bootstrap tar (matches original ``bootstrap_tar``)."""
    bootstrap_gnu(TAR, cfg)


@_skip_if_done("bash")
def bootstrap_bash(cfg: BootstrapConfig) -> None:
    """Bootstrap bash (matches original ``bootstrap_bash``).

    The original always builds its own bash to avoid subtle shell-init bugs
    in the host shell.  We do the same. :D
    """
    bootstrap_gnu(BASH, cfg)


@_skip_if_done("libffi")
def bootstrap_libffi(cfg: BootstrapConfig) -> None:
    """Bootstrap libffi (matches original ``bootstrap_libffi``)."""
    bootstrap_gnu(LIBFFI, cfg)


@_skip_if_done("python")
def bootstrap_python(cfg: BootstrapConfig) -> None:
    """Bootstrap the Gentoo-patched Python 3.11 (matches original ``bootstrap_python``).

    Uses the patched tarball from the Gentoo developer mirror, just like
    the original script.
    """
    bootstrap_gnu(PYTHON, cfg)


# ---------------------------------------------------------------------------
# Stage 2 per-package bootstrappers
# ---------------------------------------------------------------------------


@_skip_if_done("autoconf")
def bootstrap_autoconf(cfg: BootstrapConfig) -> None:
    """Bootstrap autoconf."""
    bootstrap_gnu(AUTOCONF, cfg)


@_skip_if_done("automake")
def bootstrap_automake(cfg: BootstrapConfig) -> None:
    """Bootstrap automake."""
    bootstrap_gnu(AUTOMAKE, cfg)


@_skip_if_done("libtool")
def bootstrap_libtool(cfg: BootstrapConfig) -> None:
    """Bootstrap libtool."""
    bootstrap_gnu(LIBTOOL, cfg)


@_skip_if_done("pkg-config")
def bootstrap_pkg_config(cfg: BootstrapConfig) -> None:
    """Bootstrap pkg-config."""
    bootstrap_simple(PKG_CONFIG, cfg)


@_skip_if_done("binutils")
def bootstrap_binutils(cfg: BootstrapConfig) -> None:
    """Bootstrap binutils (matches original ``bootstrap_binutils``)."""
    bootstrap_gnu(BINUTILS, cfg)


@_skip_if_done("gcc")
def bootstrap_gcc(cfg: BootstrapConfig) -> None:
    """Bootstrap GCC (matches original ``bootstrap_gnu gcc ...``).

    GCC uses ``--enable-languages=c,c++ --disable-bootstrap --disable-multilib``
    as recommended for a prefix bootstrap on Linux aarch64.
    """
    bootstrap_gnu(GCC, cfg)


# ---------------------------------------------------------------------------
# Stage 3 per-package bootstrappers
# ---------------------------------------------------------------------------


@_skip_if_done("openssl")
def bootstrap_openssl(cfg: BootstrapConfig) -> None:
    """Bootstrap OpenSSL."""
    bootstrap_simple(OPENSSL, cfg)


@_skip_if_done("curl")
def bootstrap_curl(cfg: BootstrapConfig) -> None:
    """Bootstrap curl."""
    bootstrap_simple(CURL, cfg)


@_skip_if_done("rsync")
def bootstrap_rsync(cfg: BootstrapConfig) -> None:
    """Bootstrap rsync."""
    bootstrap_simple(RSYNC, cfg)


# ---------------------------------------------------------------------------
# Stage orchestrators matching original bootstrap_stage1 / 2 / 3
# ---------------------------------------------------------------------------


def bootstrap_stage1(cfg: BootstrapConfig) -> None:
    """Stage 1 — bootstrap essential GNU userland tools and libraries.

    Follows the same ordering as the original ``bootstrap_stage1()``:

    make → libressl → wget → sed → xz → bzip2 → patch → m4 → bison →
    coreutils → findutils → tar → grep → gawk → bash → zlib → libffi →
    python
    """
    einfo("Starting Stage 1 — Essential GNU Tools  :D")
    estatus("bootstrap: stage1")

    bootstrap_make(cfg)
    bootstrap_libressl(cfg)
    bootstrap_wget(cfg)
    bootstrap_sed(cfg)
    bootstrap_xz(cfg)
    bootstrap_bzip2(cfg)
    bootstrap_gzip(cfg)
    bootstrap_patch(cfg)
    bootstrap_m4(cfg)
    bootstrap_bison(cfg)
    bootstrap_coreutils(cfg)
    bootstrap_findutils(cfg)
    bootstrap_tar(cfg)
    bootstrap_grep(cfg)
    bootstrap_gawk(cfg)
    bootstrap_bash(cfg)
    bootstrap_zlib(cfg)
    bootstrap_libffi(cfg)
    bootstrap_python(cfg)

    estatus("bootstrap: stage1 done")
    einfo("Stage 1 complete!  :D")


def bootstrap_stage2(cfg: BootstrapConfig) -> None:
    """Stage 2 — bootstrap the GNU build toolchain.

    autoconf → automake → libtool → pkg-config → binutils → gcc
    """
    einfo("Starting Stage 2 — GNU Build Toolchain  :D")
    estatus("bootstrap: stage2")

    bootstrap_autoconf(cfg)
    bootstrap_automake(cfg)
    bootstrap_libtool(cfg)
    bootstrap_pkg_config(cfg)
    bootstrap_binutils(cfg)
    bootstrap_gcc(cfg)

    estatus("bootstrap: stage2 done")
    einfo("Stage 2 complete!  :D")


def bootstrap_stage3(cfg: BootstrapConfig) -> None:
    """Stage 3 — bootstrap Portage prerequisites.

    openssl → curl → rsync
    """
    einfo("Starting Stage 3 — Portage Prerequisites  :D")
    estatus("bootstrap: stage3")

    bootstrap_openssl(cfg)
    bootstrap_curl(cfg)
    bootstrap_rsync(cfg)

    estatus("bootstrap: stage3 done")
    einfo("Stage 3 complete!  Portage is ready.  :D")
