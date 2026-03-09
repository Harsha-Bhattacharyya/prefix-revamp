"""Tests for prefix_bootstrap.extractor."""

from __future__ import annotations

import io
import tarfile
import tempfile
from pathlib import Path

import pytest

from prefix_bootstrap.extractor import ExtractionError, extract


def _make_tarball(dest_dir: Path, top_dir: str, files: dict[str, bytes]) -> Path:
    """Create a .tar.gz at *dest_dir* with the given *files* under *top_dir*."""
    tarball = dest_dir / f"{top_dir}.tar.gz"
    with tarfile.open(str(tarball), "w:gz") as tf:
        for name, data in files.items():
            info = tarfile.TarInfo(name=f"{top_dir}/{name}")
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return tarball


class TestExtract:
    def test_basic_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tarball = _make_tarball(
                tmp_path,
                "hello-1.0",
                {"configure": b"#!/bin/sh\necho hello", "Makefile": b"all:"},
            )
            dest = tmp_path / "build"
            result = extract(tarball, dest)
            assert result == dest / "hello-1.0"
            assert (result / "configure").exists()
            assert (result / "Makefile").exists()

    def test_not_a_tarball_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "not.tar.gz"
            bad.write_bytes(b"this is not a tarball")
            with pytest.raises(ExtractionError, match="valid tar archive"):
                extract(bad, Path(tmp) / "out")

    def test_unsafe_absolute_path_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tarball = tmp_path / "evil.tar.gz"
            with tarfile.open(str(tarball), "w:gz") as tf:
                info = tarfile.TarInfo(name="/etc/passwd")
                info.size = 5
                tf.addfile(info, io.BytesIO(b"evil!"))
            with pytest.raises(ExtractionError, match="Unsafe path"):
                extract(tarball, tmp_path / "out")

    def test_unsafe_dotdot_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tarball = tmp_path / "dotdot.tar.gz"
            with tarfile.open(str(tarball), "w:gz") as tf:
                info = tarfile.TarInfo(name="pkg/../../../etc/passwd")
                info.size = 5
                tf.addfile(info, io.BytesIO(b"evil!"))
            with pytest.raises(ExtractionError, match="Unsafe path"):
                extract(tarball, tmp_path / "out")

    def test_creates_dest_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tarball = _make_tarball(tmp_path, "pkg-2.0", {"file.txt": b"data"})
            dest = tmp_path / "deep" / "nested" / "dir"
            extract(tarball, dest)
            assert dest.is_dir()
