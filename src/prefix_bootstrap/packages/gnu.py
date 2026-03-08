"""
prefix_bootstrap.packages.gnu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Async GNU mirror scraper.

``resolve_latest(project, mirror)`` fetches the directory listing for a GNU
project and returns the highest stable version along with its download URL.
This is used at runtime to optionally upgrade the hard-coded baseline
versions in ``definitions.py`` to the latest upstream release.

Example::

    import asyncio
    from prefix_bootstrap.packages.gnu import resolve_latest

    url, version = asyncio.run(resolve_latest("bash"))
    # url  == "https://ftpmirror.gnu.org/bash/bash-5.2.21.tar.gz"
    # version == "5.2.21"
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING

import aiohttp
import structlog

if TYPE_CHECKING:
    pass

log = structlog.get_logger(__name__)

# Pattern that matches ``<name>-<version>.tar.{xz,gz,bz2}`` filenames in
# an Apache/nginx directory listing or GNU mirror HTML page.
_TARBALL_RE = re.compile(
    r'href="(?P<name>[a-z][a-z0-9._-]+)-(?P<version>\d[\d.]+)\.tar\.(?:xz|gz|bz2)"',
    re.IGNORECASE,
)


# Simple semantic-version comparison key: split on dots, zero-pad to 4 parts.
def _version_key(version: str) -> tuple[int, ...]:
    parts = re.split(r"[.\-]", version)
    ints = []
    for p in parts[:4]:
        try:
            ints.append(int(p))
        except ValueError:
            ints.append(0)
    while len(ints) < 4:
        ints.append(0)
    return tuple(ints)


async def resolve_latest(
    project: str,
    mirror: str = "https://ftpmirror.gnu.org",
    *,
    session: aiohttp.ClientSession | None = None,
    timeout: int = 15,
) -> tuple[str, str]:
    """Return ``(url, version)`` for the latest stable tarball of *project*.

    Parameters
    ----------
    project:
        GNU project name, e.g. ``"bash"``.
    mirror:
        Base URL of the GNU mirror.
    session:
        Optional existing ``aiohttp.ClientSession`` to reuse.
    timeout:
        HTTP request timeout in seconds.

    Returns
    -------
    tuple[str, str]
        ``(url, version)`` where *url* is the full download URL for a
        ``.tar.xz`` (preferred) or ``.tar.gz`` tarball, and *version* is the
        parsed version string.

    Raises
    ------
    RuntimeError
        If no suitable tarball is found in the directory listing.
    """
    listing_url = f"{mirror.rstrip('/')}/{project}/"
    log.debug("gnu.resolve_latest.fetch", url=listing_url)

    _session = session or aiohttp.ClientSession()
    try:
        async with _session.get(listing_url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            html = await resp.text()
    finally:
        if session is None:
            await _session.close()

    candidates: dict[str, str] = {}  # version -> filename
    for m in _TARBALL_RE.finditer(html):
        fname = m.group(0).split('"')[1]
        ver = m.group("version")
        # Prefer .tar.xz over .tar.gz.
        if ver not in candidates or fname.endswith(".tar.xz"):
            candidates[ver] = fname

    if not candidates:
        raise RuntimeError(f"No tarballs found for GNU project '{project}' at {listing_url} :/")

    best_version = max(candidates, key=_version_key)
    filename = candidates[best_version]
    url = f"{mirror.rstrip('/')}/{project}/{filename}"
    log.info("gnu.resolve_latest.found", project=project, version=best_version, url=url)
    return url, best_version


async def resolve_all_latest(
    projects: list[str],
    mirror: str = "https://ftpmirror.gnu.org",
    *,
    timeout: int = 15,
) -> dict[str, tuple[str, str]]:
    """Resolve the latest version for each project concurrently.

    Parameters
    ----------
    projects:
        List of GNU project names.
    mirror:
        GNU mirror base URL.
    timeout:
        Per-request timeout in seconds.

    Returns
    -------
    dict[str, tuple[str, str]]
        Mapping of ``project_name -> (url, version)``.
    """
    async with aiohttp.ClientSession() as session:
        tasks = {
            name: asyncio.create_task(
                resolve_latest(name, mirror, session=session, timeout=timeout)
            )
            for name in projects
        }
        results: dict[str, tuple[str, str]] = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as exc:  # noqa: BLE001
                log.warning("gnu.resolve_latest.failed", project=name, error=str(exc))
        return results
