"""Tests for prefix_bootstrap.packages.gnu (URL resolution logic only)."""

from __future__ import annotations

from prefix_bootstrap.packages.gnu import _version_key


class TestVersionKey:
    def test_simple(self) -> None:
        assert _version_key("1.2.3") == (1, 2, 3, 0)

    def test_patch(self) -> None:
        assert _version_key("5.2.21") == (5, 2, 21, 0)

    def test_ordering(self) -> None:
        versions = ["1.9.0", "2.0.0", "1.10.0", "1.9.1"]
        assert sorted(versions, key=_version_key) == [
            "1.9.0",
            "1.9.1",
            "1.10.0",
            "2.0.0",
        ]

    def test_four_parts(self) -> None:
        assert _version_key("1.2.3.4") == (1, 2, 3, 4)

    def test_non_numeric_part(self) -> None:
        key = _version_key("1.2.alpha")
        assert key[0] == 1
        assert key[1] == 2
        assert key[2] == 0  # non-numeric -> 0
