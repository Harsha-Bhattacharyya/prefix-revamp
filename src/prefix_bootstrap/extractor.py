"""
prefix_bootstrap.extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~

Tarball extraction helpers (backed by the stdlib ``tarfile`` module).

``extract(tarball, dest)`` unpacks a ``.tar.xz``, ``.tar.gz``, or
``.tar.bz2`` archive into *dest*, stripping the top-level directory so
that the extracted source tree sits directly in *dest*.

Example::

    from pathlib import Path
    from prefix_bootstrap.extractor import extract

    src_dir = extract(
        tarball=Path("/tmp/bootstrap/distfiles/bash-5.2.21.tar.xz"),
        dest=Path("/tmp/bootstrap/build/bash"),
    )
    # src_dir == Path("/tmp/bootstrap/build/bash/bash-5.2.21")
"""

from __future__ import annotations

import tarfile
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)


class ExtractionError(RuntimeError):
    """Raised when a tarball cannot be extracted safely."""


def extract(tarball: Path, dest: Path) -> Path:
    """Extract *tarball* into *dest* and return the source directory.

    The archive's top-level directory is preserved as a sub-directory of
    *dest*.  Absolute paths and directory-traversal members (``../``) are
    rejected to prevent archive-bomb attacks.

    Parameters
    ----------
    tarball:
        Path to the compressed tarball.
    dest:
        Directory under which the tarball is unpacked.  Created if absent.

    Returns
    -------
    Path
        The extracted source directory (``dest/<top-level-dir>``).

    Raises
    ------
    ExtractionError
        If the tarball contains unsafe paths or cannot be read.
    """
    dest.mkdir(parents=True, exist_ok=True)
    log.info("extractor.start", tarball=str(tarball), dest=str(dest))

    if not tarfile.is_tarfile(str(tarball)):
        raise ExtractionError(f"Not a valid tar archive: {tarball} :/")

    with tarfile.open(str(tarball)) as tf:
        _check_members(tf, tarball)
        top_level = _find_top_level(tf, tarball)
        tf.extractall(path=str(dest), filter="tar")

    extracted = dest / top_level
    log.info("extractor.done", src_dir=str(extracted))
    return extracted


def _check_members(tf: tarfile.TarFile, tarball: Path) -> None:
    """Reject unsafe archive members."""
    for member in tf.getmembers():
        if member.name.startswith("/") or ".." in Path(member.name).parts:
            raise ExtractionError(f"Unsafe path '{member.name}' in {tarball.name}.  Aborting. :/")


def _find_top_level(tf: tarfile.TarFile, tarball: Path) -> str:
    """Return the top-level directory name inside the archive."""
    names = tf.getnames()
    if not names:
        raise ExtractionError(f"Archive {tarball.name} is empty. :/")

    top_dirs = {name.split("/")[0] for name in names}
    if len(top_dirs) != 1:
        raise ExtractionError(
            f"Archive {tarball.name} has multiple top-level entries: {top_dirs}.  "
            "Expected a single source directory. :/"
        )
    return top_dirs.pop()
