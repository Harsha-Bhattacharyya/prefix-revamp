"""
prefix_bootstrap.downloader
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Async download engine with rich progress bars.

Usage::

    import asyncio
    from pathlib import Path
    from prefix_bootstrap.downloader import Downloader
    from prefix_bootstrap.config import BootstrapConfig

    cfg = BootstrapConfig(prefix=Path("/usr/local/gentoo"), work_dir=Path("/tmp/bootstrap"))
    dl  = Downloader(cfg)
    asyncio.run(dl.fetch_all(packages))

Each package is downloaded to ``cfg.downloads_dir / package.tarball_name``.
If the file already exists *and* its checksum matches, the download is skipped
(i.e. resumable / idempotent).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiohttp
import structlog
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from prefix_bootstrap.config import BootstrapConfig
from prefix_bootstrap.hasher import verify_md5, verify_sha256
from prefix_bootstrap.packages.base import ChecksumKind, Package

log = structlog.get_logger(__name__)

_CHUNK_SIZE = 65_536  # 64 KiB


class DownloadError(RuntimeError):
    """Raised when a package cannot be fetched after all retries."""


class Downloader:
    """Manages async parallel downloads with rich progress display.

    Parameters
    ----------
    config:
        The active :class:`~prefix_bootstrap.config.BootstrapConfig`.
    """

    def __init__(self, config: BootstrapConfig) -> None:
        self._cfg = config
        self._sem = asyncio.Semaphore(config.parallel_downloads)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def fetch_all(self, packages: list[Package]) -> None:
        """Download *all* packages, displaying a rich progress table.

        Already-cached files with valid checksums are skipped.  Failed
        downloads raise :class:`DownloadError`.

        Parameters
        ----------
        packages:
            List of packages to download.
        """
        self._cfg.downloads_dir.mkdir(parents=True, exist_ok=True)

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[name]}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            transient=True,
        )

        with progress:
            async with aiohttp.ClientSession(
                headers={"User-Agent": "prefix-bootstrap/0.1 (+github)"}
            ) as session:
                tasks = [self._schedule(pkg, session, progress) for pkg in packages]
                await asyncio.gather(*tasks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _schedule(
        self,
        pkg: Package,
        session: aiohttp.ClientSession,
        progress: Progress,
    ) -> None:
        dest = self._cfg.downloads_dir / pkg.tarball_name

        if dest.exists() and self._checksum_ok(dest, pkg):
            log.info("downloader.cache_hit", package=pkg.name, file=str(dest))
            return

        task_id = progress.add_task("download", name=pkg.name, total=None, start=False)

        urls = [pkg.url, *pkg.mirror_urls]
        last_exc: Exception | None = None

        for url in urls:
            for attempt in range(self._cfg.retries + 1):
                try:
                    async with self._sem:
                        await self._fetch_url(url, dest, session, progress, task_id)
                    break
                except (aiohttp.ClientError, OSError) as exc:
                    last_exc = exc
                    log.warning(
                        "downloader.retry",
                        package=pkg.name,
                        url=url,
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    await asyncio.sleep(min(2**attempt, 30))
            else:
                continue
            break
        else:
            raise DownloadError(
                f"Failed to download {pkg.name} after trying all URLs/retries. "
                f"Last error: {last_exc} :/"
            )

        progress.remove_task(task_id)

        if not self._checksum_ok(dest, pkg):
            dest.unlink(missing_ok=True)
            raise DownloadError(
                f"Checksum mismatch for {pkg.name} ({dest}).  "
                "The downloaded file may be corrupt. :/"
            )

        log.info("downloader.complete", package=pkg.name, file=str(dest))

    async def _fetch_url(
        self,
        url: str,
        dest: Path,
        session: aiohttp.ClientSession,
        progress: Progress,
        task_id: TaskID,
    ) -> None:
        log.debug("downloader.start", url=url, dest=str(dest))
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=600)) as resp:
            resp.raise_for_status()
            total = resp.content_length
            progress.update(task_id, total=total)
            progress.start_task(task_id)

            with dest.open("wb") as fh:
                async for chunk in resp.content.iter_chunked(_CHUNK_SIZE):
                    fh.write(chunk)
                    progress.update(task_id, advance=len(chunk))

    def _checksum_ok(self, path: Path, pkg: Package) -> bool:
        """Return True if *path* satisfies at least one of *pkg*'s checksums."""
        if self._cfg.skip_verify:
            return True
        if not pkg.checksums:
            return True
        for cs in pkg.checksums:
            if cs.kind == ChecksumKind.SHA256:
                ok = verify_sha256(str(path), cs.value)
            elif cs.kind == ChecksumKind.MD5:
                ok = verify_md5(str(path), cs.value)
            else:
                continue
            if not ok:
                log.error(
                    "downloader.checksum_failed",
                    package=pkg.name,
                    kind=cs.kind,
                    expected=cs.value,
                )
                return False
        return True
