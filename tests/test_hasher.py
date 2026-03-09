"""Tests for prefix_bootstrap.hasher (pure-Python path)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from prefix_bootstrap.hasher import md5_file, sha256_file, verify_md5, verify_sha256


class TestHasher:
    def test_sha256_matches_hashlib(self, tmp_path: Path) -> None:
        data = b"Hello, Gentoo! :D"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert sha256_file(str(p)) == expected

    def test_md5_matches_hashlib(self, tmp_path: Path) -> None:
        data = b"prefix bootstrap test :)"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        expected = hashlib.md5(data).hexdigest()  # noqa: S324
        assert md5_file(str(p)) == expected

    def test_verify_sha256_true(self, tmp_path: Path) -> None:
        data = b"correct"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        assert verify_sha256(str(p), digest) is True

    def test_verify_sha256_false(self, tmp_path: Path) -> None:
        data = b"incorrect"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        assert verify_sha256(str(p), "0" * 64) is False

    def test_verify_md5_true(self, tmp_path: Path) -> None:
        data = b"md5test"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        digest = hashlib.md5(data).hexdigest()  # noqa: S324
        assert verify_md5(str(p), digest) is True

    def test_verify_md5_false(self, tmp_path: Path) -> None:
        data = b"md5fail"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        assert verify_md5(str(p), "0" * 32) is False

    def test_case_insensitive(self, tmp_path: Path) -> None:
        data = b"case"
        p = tmp_path / "test.bin"
        p.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest().upper()
        assert verify_sha256(str(p), digest) is True

    def test_large_file(self, tmp_path: Path) -> None:
        data = b"x" * (3 * 1024 * 1024)  # 3 MiB
        p = tmp_path / "large.bin"
        p.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert sha256_file(str(p)) == expected
