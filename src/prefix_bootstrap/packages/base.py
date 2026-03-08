"""
prefix_bootstrap.packages.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pydantic models that describe a source package to be fetched and built.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class ChecksumKind(StrEnum):
    """Supported checksum algorithms."""

    SHA256 = "sha256"
    MD5 = "md5"


class Checksum(BaseModel):
    """A single expected checksum for a downloaded file."""

    kind: ChecksumKind
    value: Annotated[str, Field(min_length=32, description="Hex digest")]


class ConfigureFlag(BaseModel):
    """A single ``./configure`` flag passed during build."""

    flag: str
    description: str = ""


class Package(BaseModel):
    """Immutable description of a source package.

    Attributes
    ----------
    name:
        Short identifier, e.g. ``bash``.
    version:
        Version string, e.g. ``5.2.21``.
    url:
        Primary download URL.
    mirror_urls:
        Fallback URLs tried in order if *url* fails.
    checksums:
        Expected checksums for the downloaded tarball.
    configure_flags:
        Extra flags passed to ``./configure`` (in addition to the standard
        ``--prefix`` and ``--host`` flags that are always added).
    env:
        Additional environment variables set during ``configure`` and ``make``.
    stage:
        Bootstrap stage in which this package is built (1, 2, or 3).
    depends:
        Names of other packages that must be installed first.
    """

    name: str
    version: str
    url: str
    mirror_urls: list[str] = Field(default_factory=list)
    checksums: list[Checksum] = Field(default_factory=list)
    configure_flags: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    stage: Annotated[int, Field(ge=1, le=3)] = 1
    depends: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}

    @property
    def tarball_name(self) -> str:
        """Filename portion of the primary URL."""
        return self.url.rsplit("/", 1)[-1]

    @property
    def source_dir_name(self) -> str:
        """Conventional unpacked source directory name (``{name}-{version}``)."""
        return f"{self.name}-{self.version}"
