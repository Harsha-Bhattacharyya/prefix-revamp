"""Tests for prefix_bootstrap.packages.definitions and .base."""

from __future__ import annotations

import pytest

from prefix_bootstrap.packages.base import Checksum, ChecksumKind, Package
from prefix_bootstrap.packages.definitions import (
    ALL_PACKAGES,
    PACKAGES_BY_NAME,
    STAGE_PACKAGES,
)


class TestPackageBase:
    def test_tarball_name(self) -> None:
        pkg = Package(
            name="bash",
            version="5.2.21",
            url="https://ftpmirror.gnu.org/bash/bash-5.2.21.tar.xz",
            stage=1,
        )
        assert pkg.tarball_name == "bash-5.2.21.tar.xz"

    def test_source_dir_name(self) -> None:
        pkg = Package(
            name="bash",
            version="5.2.21",
            url="https://example.com/bash-5.2.21.tar.gz",
            stage=1,
        )
        assert pkg.source_dir_name == "bash-5.2.21"

    def test_invalid_stage(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Package(name="x", version="1.0", url="https://x.com/x.tar.gz", stage=0)

    def test_frozen(self) -> None:
        from pydantic import ValidationError

        pkg = Package(name="x", version="1.0", url="https://x.com/x.tar.gz", stage=1)
        with pytest.raises(ValidationError):
            pkg.version = "2.0"  # type: ignore[misc]

    def test_checksum_model(self) -> None:
        cs = Checksum(kind=ChecksumKind.SHA256, value="a" * 64)
        assert cs.kind == ChecksumKind.SHA256


class TestDefinitions:
    def test_all_packages_non_empty(self) -> None:
        assert len(ALL_PACKAGES) > 0

    def test_packages_by_name_consistent(self) -> None:
        assert len(PACKAGES_BY_NAME) == len(ALL_PACKAGES)
        for pkg in ALL_PACKAGES:
            assert pkg.name in PACKAGES_BY_NAME

    def test_stage_packages_cover_all(self) -> None:
        all_staged = [p for ps in STAGE_PACKAGES.values() for p in ps]
        assert {p.name for p in all_staged} == {p.name for p in ALL_PACKAGES}

    def test_stage_keys(self) -> None:
        assert set(STAGE_PACKAGES.keys()) == {1, 2, 3}

    def test_all_packages_have_valid_stages(self) -> None:
        for pkg in ALL_PACKAGES:
            assert pkg.stage in {1, 2, 3}, f"{pkg.name} has invalid stage {pkg.stage}"

    def test_all_dependencies_resolvable(self) -> None:
        known = {p.name for p in ALL_PACKAGES}
        for pkg in ALL_PACKAGES:
            for dep in pkg.depends:
                assert dep in known, f"{pkg.name} depends on '{dep}' which is not in the catalogue"

    def test_essential_packages_present(self) -> None:
        expected = {"bash", "coreutils", "make", "tar", "gcc", "binutils"}
        names = {p.name for p in ALL_PACKAGES}
        assert expected <= names
