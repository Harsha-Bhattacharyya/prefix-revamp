# cython: language_level=3, boundscheck=False, wraparound=False
"""
prefix_bootstrap._cython.hasher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cython-accelerated file-hashing utilities.

Two functions are exposed:

* ``sha256_file(path: str) -> str``   — hex-digest of a file's SHA-256 hash.
* ``md5_file(path: str) -> str``      — hex-digest of a file's MD5 hash.

Both stream the file in 1 MiB chunks, so large tarballs are handled
without loading them entirely into memory.
"""

import hashlib


def sha256_file(path: str) -> str:
    """Return the lowercase hex SHA-256 digest of the file at *path*."""
    h = hashlib.sha256()
    cdef int chunk_size = 1 << 20  # 1 MiB
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: str) -> str:
    """Return the lowercase hex MD5 digest of the file at *path*."""
    h = hashlib.md5()  # noqa: S324 — used only for legacy checksum compatibility
    cdef int chunk_size = 1 << 20  # 1 MiB
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
