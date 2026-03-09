"""
prefix_bootstrap.config
~~~~~~~~~~~~~~~~~~~~~~~~

Pydantic-validated runtime configuration.

The ``BootstrapConfig`` model is the single authoritative description of
every knob that controls a bootstrap run.  It is constructed from CLI
flags by ``prefix_bootstrap.cli`` and then passed around as a frozen
value object.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# Only aarch64/arm64 is supported.
SUPPORTED_ARCH = "aarch64"

# Default GNU mirror — will be used for all GNU package downloads.
DEFAULT_GNU_MIRROR = "https://ftpmirror.gnu.org"

# Number of parallel download workers.
DEFAULT_PARALLEL = 4

# Default download retry count.
DEFAULT_RETRIES = 3


class BootstrapConfig(BaseModel):
    """Immutable configuration for a single bootstrap run.

    Attributes
    ----------
    prefix:
        Absolute path to the Gentoo Prefix root (``$EPREFIX``).
    work_dir:
        Scratch directory for downloads and build trees.
    arch:
        CPU architecture.  Must be ``aarch64``.
    chost:
        GNU configure-style host triplet derived from *arch*.
    gnu_mirror:
        Base URL of the GNU FTP mirror to use.
    parallel_downloads:
        Maximum number of concurrent HTTP connections.
    retries:
        Number of times to retry a failed download.
    log_level:
        Python logging level name.
    json_logs:
        Emit JSON log lines instead of human-readable output.
    skip_verify:
        Skip checksum verification (not recommended).
    stages:
        Which bootstrap stages to run.  Defaults to all three.
    """

    prefix: Annotated[Path, Field(description="Gentoo Prefix root ($EPREFIX)")]
    work_dir: Annotated[Path, Field(description="Scratch / build directory")]
    arch: Annotated[str, Field(default=SUPPORTED_ARCH, description="CPU architecture")]
    chost: Annotated[str, Field(default="", description="GNU host triplet (auto-derived)")]
    gnu_mirror: Annotated[
        str, Field(default=DEFAULT_GNU_MIRROR, description="GNU FTP mirror base URL")
    ]
    parallel_downloads: Annotated[
        int,
        Field(
            default=DEFAULT_PARALLEL,
            ge=1,
            le=32,
            description="Max concurrent downloads",
        ),
    ]
    retries: Annotated[
        int, Field(default=DEFAULT_RETRIES, ge=0, le=10, description="Download retry count")
    ]
    log_level: Annotated[str, Field(default="INFO", description="Logging verbosity")]
    json_logs: Annotated[bool, Field(default=False, description="Emit JSON log lines")]
    skip_verify: Annotated[bool, Field(default=False, description="Skip checksum verification")]
    stages: Annotated[
        list[int],
        Field(default_factory=lambda: [1, 2, 3], description="Bootstrap stages to execute"),
    ]

    model_config = {"frozen": True}

    @field_validator("arch")
    @classmethod
    def _validate_arch(cls, v: str) -> str:
        if v != SUPPORTED_ARCH:
            raise ValueError(
                f"Architecture '{v}' is not supported.  "
                f"Only '{SUPPORTED_ARCH}' (arm64) is supported. :/"
            )
        return v

    @field_validator("stages")
    @classmethod
    def _validate_stages(cls, v: list[int]) -> list[int]:
        allowed = {1, 2, 3}
        bad = set(v) - allowed
        if bad:
            raise ValueError(f"Unknown stage(s): {bad}.  Valid stages are 1, 2, 3.")
        return sorted(set(v))

    @model_validator(mode="after")
    def _derive_chost(self) -> BootstrapConfig:
        if not self.chost:
            # Bypass frozen model to set the derived value.
            object.__setattr__(self, "chost", f"{self.arch}-unknown-linux-gnu")
        return self

    @property
    def downloads_dir(self) -> Path:
        """Directory where downloaded tarballs are stored."""
        return self.work_dir / "distfiles"

    @property
    def build_dir(self) -> Path:
        """Root build directory (one sub-dir per package)."""
        return self.work_dir / "build"

    @property
    def tools_dir(self) -> Path:
        """Temporary tools directory (Stage 1 outputs)."""
        return self.work_dir / "tools"
