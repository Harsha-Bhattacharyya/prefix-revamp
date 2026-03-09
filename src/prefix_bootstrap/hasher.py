"""
prefix_bootstrap.hasher
~~~~~~~~~~~~~~~~~~~~~~~~

Hash-verification helpers.

Tries to import the fast Cython-compiled extension; falls back to a pure
Python implementation when the extension is not available (e.g. during
development without a build step).
"""

from __future__ import annotations

try:
    from prefix_bootstrap._cython.hasher import (  # type: ignore[import-untyped]
        md5_file,
        sha256_file,
    )
except ImportError:  # pragma: no cover — pure-Python fallback
    import hashlib

    def sha256_file(path: str) -> str:
        """Return the lowercase hex SHA-256 digest of the file at *path*."""
        h = hashlib.sha256()
        _hash_file(h, path)
        return h.hexdigest()

    def md5_file(path: str) -> str:
        """Return the lowercase hex MD5 digest of the file at *path*."""
        h = hashlib.md5()  # noqa: S324
        _hash_file(h, path)
        return h.hexdigest()

    def _hash_file(h: hashlib._Hash, path: str) -> None:
        with open(path, "rb") as fh:
            while chunk := fh.read(1 << 20):
                h.update(chunk)


def verify_sha256(path: str, expected: str) -> bool:
    """Return *True* if the SHA-256 digest of *path* matches *expected*.

    Parameters
    ----------
    path:
        File to verify.
    expected:
        Expected lowercase hex digest.
    """
    actual: str = sha256_file(path)
    return actual.lower() == expected.lower()


def verify_md5(path: str, expected: str) -> bool:
    """Return *True* if the MD5 digest of *path* matches *expected*."""
    actual: str = md5_file(path)
    return actual.lower() == expected.lower()


__all__ = ["sha256_file", "md5_file", "verify_sha256", "verify_md5"]
