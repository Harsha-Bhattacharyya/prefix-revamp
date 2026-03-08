"""
prefix_bootstrap.packages.definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The catalogue of source packages required for a Gentoo Prefix aarch64
bootstrap, matching the phasing and package selection of the original
``bootstrap-prefix.sh`` script.

Stage 1 — essential userland + libraries (bash, coreutils, findutils, grep,
           sed, gawk, make, patch, tar, xz, bzip2, m4, bison, wget,
           libressl, zlib, libffi, python).
Stage 2 — build toolchain (autoconf, automake, libtool, pkg-config,
           binutils, gcc).
Stage 3 — Portage prerequisites (curl, rsync).

Version fallbacks from the original script are encoded as ``mirror_urls``
so the downloader can try alternatives automatically.
"""

from __future__ import annotations

from prefix_bootstrap.packages.base import Checksum, ChecksumKind, Package

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GNU = "https://ftpmirror.gnu.org"
_TUKAANI = "https://tukaani.org/xz"
_PYTHON_DEV = "https://dev.gentoo.org/~grobian/distfiles"


def _gnu(project: str, version: str, ext: str = "tar.xz") -> str:
    """Return a ftpmirror.gnu.org URL for a GNU project tarball."""
    return f"{_GNU}/{project}/{project}-{version}.{ext}"


# ---------------------------------------------------------------------------
# Stage 1 — essential tools and libraries
# ---------------------------------------------------------------------------

ZLIB = Package(
    name="zlib",
    version="1.3.1",
    url="https://zlib.net/zlib-1.3.1.tar.gz",
    mirror_urls=[
        "https://sourceware.org/pub/zlib/zlib-1.3.1.tar.gz",
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23",
        )
    ],
    configure_flags=["--static"],
    stage=1,
)

BZIP2 = Package(
    name="bzip2",
    version="1.0.8",
    url="https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269",
        )
    ],
    stage=1,
)

XZ = Package(
    name="xz",
    version="5.4.5",
    url=f"{_TUKAANI}/xz-5.4.5.tar.xz",
    mirror_urls=[
        f"{_TUKAANI}/xz-5.2.4.tar.xz",
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="da9dec6c12cf2ecf269c31ab30b6c2a171b6b810f2fd69019a5ef1a3b0b5c770",
        )
    ],
    configure_flags=["--disable-nls", "--disable-assembler"],
    stage=1,
)

# libressl: used to bootstrap wget over TLS — original uses 3.4.3 then fallbacks
LIBRESSL = Package(
    name="libressl",
    version="3.4.3",
    url="https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/libressl-3.4.3.tar.gz",
    mirror_urls=[
        "https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/libressl-3.2.4.tar.gz",
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="8b031b2020a1936bc8e30fd6c83ccfd78dcc56e0d6a5ed1c4df1b9e03e9d60cb",
        )
    ],
    configure_flags=[
        "--enable-static",
        "--disable-shared",
    ],
    stage=1,
)

MAKE = Package(
    name="make",
    version="4.2.1",
    url=_gnu("make", "4.2.1"),
    mirror_urls=[_gnu("make", "4.4.1")],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="d6e262bf3601b42d2b1e4ef8310029e1dcf20083c5446b4b7aa67081fdffc589",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

WGET = Package(
    name="wget",
    version="1.25.0",
    url=_gnu("wget", "1.25.0"),
    mirror_urls=[
        _gnu("wget", "1.20.1"),
        _gnu("wget", "1.17.1"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="81542f5cefb8faacc39bbbc6c82ded80e3e4a88505ae72ea51df27525bcde04c",
        )
    ],
    configure_flags=["--disable-nls", "--without-ssl"],
    stage=1,
    depends=["libressl"],
)

SED = Package(
    name="sed",
    version="4.9",
    url=_gnu("sed", "4.9"),
    mirror_urls=[_gnu("sed", "4.5", "tar.gz")],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="6e226b732e1cd739464ad6862bd1a1aba42d7982922da7a53519631d24975181",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

PATCH = Package(
    name="patch",
    version="2.8",
    url=_gnu("patch", "2.8"),
    mirror_urls=[
        _gnu("patch", "2.7.5"),
        _gnu("patch", "2.6.1"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="3b1a21cfc5c7e5db6b06bdfb1cde53b29e1ae1b4e57ed71ec21b0aaa5498c17c",
        )
    ],
    stage=1,
)

M4 = Package(
    name="m4",
    version="1.4.20",
    url=_gnu("m4", "1.4.20"),
    mirror_urls=[_gnu("m4", "1.4.19")],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="e236c4dbe44d209e0bfc493ae2d3cd37bfc3d5eb49b4f3dfa8c12a31d37dc71a",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

BISON = Package(
    name="bison",
    version="3.8.2",
    url=_gnu("bison", "3.8.2"),
    mirror_urls=[
        _gnu("bison", "2.6.2"),
        _gnu("bison", "2.5.1"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="9bba0214ccf7f1079c5d59210045227bcf619519840ebfa80cd3849cff5a5bf2",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
    depends=["m4"],
)

GREP = Package(
    name="grep",
    version="3.12",
    url=_gnu("grep", "3.12"),
    mirror_urls=[
        _gnu("grep", "3.3"),
        _gnu("grep", "3.11"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="a76d30aa9a0e0d9ac5e3ddc5a64b09e9f0a3b9fdef89d1cc3e6b0aeccc5a6fdc",
        )
    ],
    configure_flags=["--disable-nls", "--disable-perl-regexp"],
    stage=1,
)

COREUTILS = Package(
    name="coreutils",
    version="9.8",
    url=_gnu("coreutils", "9.8"),
    mirror_urls=[
        _gnu("coreutils", "9.5"),
        _gnu("coreutils", "8.32"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="f943cd7a679ea4f872f56a7b85d03c5b2c4378a63bae7f36c46e14e19e4c5b7e",
        )
    ],
    configure_flags=[
        "--disable-nls",
        "--disable-acl",
        "--without-gmp",
        "--enable-no-install-program=stdbuf",
    ],
    stage=1,
)

FINDUTILS = Package(
    name="findutils",
    version="4.10.0",
    url=_gnu("findutils", "4.10.0"),
    mirror_urls=[_gnu("findutils", "4.9.0")],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="1387e0b67ff247d2abde998f90dfbf70c1491391a59ddfecb8ae698789f0a4f5",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

GAWK = Package(
    name="gawk",
    version="5.3.2",
    url=_gnu("gawk", "5.3.2"),
    mirror_urls=[
        _gnu("gawk", "5.0.1"),
        _gnu("gawk", "4.0.1"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="46c16b8e3e36b21a9bb5e4c6b22f73ac5a97e8e977e72a0dd95beea42e4f3a59",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

TAR = Package(
    name="tar",
    version="1.35",
    url=_gnu("tar", "1.35"),
    mirror_urls=[_gnu("tar", "1.32")],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="4d62ff37342ec7aed748535323930c7cf94acf71c3591882b26a7ea50f3edc16",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
    depends=["xz", "bzip2"],
)

GZIP = Package(
    name="gzip",
    version="1.14",
    url=_gnu("gzip", "1.14"),
    mirror_urls=[_gnu("gzip", "1.4")],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="01a7a9eb6bc15f8b5def46af92b9e6ece0cc39fdb15af0a8a5b15a0cfeef4cb8",
        )
    ],
    stage=1,
)

BASH = Package(
    name="bash",
    version="5.3",
    url=_gnu("bash", "5.3"),
    mirror_urls=[
        _gnu("bash", "5.2"),
        _gnu("bash", "5.1"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="58bc00da9c6fb3c50a58ab57219df8c0c7a2437cfd1c7d03c33c10cd498e4e8e",
        )
    ],
    configure_flags=[
        "--without-bash-malloc",
        "--disable-nls",
    ],
    stage=1,
)

LIBFFI = Package(
    name="libffi",
    version="3.4.8",
    url=_gnu("libffi", "3.4.8"),
    mirror_urls=[
        _gnu("libffi", "3.3"),
        _gnu("libffi", "3.2.1"),
    ],
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="bc9842a18898bfacb0ed1252c4feb6a6fb6de32b4f0e090bbed7ce5dc2f23994",
        )
    ],
    configure_flags=["--libdir=${ROOT}/tmp/usr/lib"],
    stage=1,
)

# Bootstrap Python (patched Gentoo version matching original script's python_ver)
PYTHON = Package(
    name="Python",
    version="3.11.7-gentoo-prefix-patched",
    url=f"{_PYTHON_DEV}/Python-3.11.7-gentoo-prefix-patched.tar.xz",
    checksums=[],
    configure_flags=[
        "--with-system-ffi",
        "--without-ensurepip",
        "--disable-ipv6",
        "--disable-shared",
    ],
    stage=1,
    depends=["zlib", "libffi"],
)

# ---------------------------------------------------------------------------
# Stage 2 — build toolchain
# ---------------------------------------------------------------------------

AUTOCONF = Package(
    name="autoconf",
    version="2.71",
    url=_gnu("autoconf", "2.71"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="431075ad0bf529ef13a91ac600f213d768f440422c2c5571e06f4b06f9cdb4e5",
        )
    ],
    stage=2,
    # m4 is a stage-1 package; stage ordering guarantees it is already present.
)

AUTOMAKE = Package(
    name="automake",
    version="1.16.5",
    url=_gnu("automake", "1.16.5"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="07bd24ad08a64bc17250ce09ec56e921d6343903943e99ccf63bbf0705e34605",
        )
    ],
    stage=2,
    depends=["autoconf"],
)

LIBTOOL = Package(
    name="libtool",
    version="2.4.7",
    url=_gnu("libtool", "2.4.7"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="04e96c2404ea70c590c546eba4202a4e12722c640016c12b9b2f1ce3d481e9a8",
        )
    ],
    stage=2,
    depends=["automake"],
)

PKG_CONFIG = Package(
    name="pkg-config",
    version="0.29.2",
    url="https://pkg-config.freedesktop.org/releases/pkg-config-0.29.2.tar.gz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="6fc69c01688c9458a57eb9a1664c9aba372ccda420a02bf4429fe610e7e7d591",
        )
    ],
    configure_flags=["--with-internal-glib"],
    stage=2,
)

BINUTILS = Package(
    name="binutils",
    version="2.42",
    url=_gnu("binutils", "2.42"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="f6e4d41fd5fc778b06b7891457b3620da5ecea1006c6a4a41ae998109f85a800",
        )
    ],
    configure_flags=[
        "--disable-nls",
        "--disable-multilib",
        "--disable-werror",
        "--enable-64-bit-bfd",
    ],
    stage=2,
)

GCC = Package(
    name="gcc",
    version="13.3.0",
    url=_gnu("gcc/gcc-13.3.0", "13.3.0"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="0845e9621c9543a13f484e94584bd5b176bcd417c722c075f66b8616a274f53f",
        )
    ],
    configure_flags=[
        "--enable-languages=c,c++",
        "--disable-bootstrap",
        "--disable-multilib",
        "--disable-nls",
        "--disable-libsanitizer",
    ],
    stage=2,
    # zlib is stage 1 — stage ordering guarantees it is present.
    depends=["binutils"],
)

# ---------------------------------------------------------------------------
# Stage 3 — Portage prerequisites
# ---------------------------------------------------------------------------

OPENSSL = Package(
    name="openssl",
    version="3.3.0",
    url="https://github.com/openssl/openssl/releases/download/openssl-3.3.0/openssl-3.3.0.tar.gz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="53e66b043322a606abf0087e7699a0e033a37fa13feb9742df35c3a33b18fb02",
        )
    ],
    configure_flags=["no-shared", "no-tests"],
    stage=3,
)

CURL = Package(
    name="curl",
    version="8.7.1",
    url="https://curl.se/download/curl-8.7.1.tar.xz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="6fea2aac6a4610fbd0400afb0bcddbe7258a64c63f1f68e5855ebc0c659710cd",
        )
    ],
    configure_flags=[
        "--without-brotli",
        "--without-hyper",
        "--with-ssl",
    ],
    stage=3,
    depends=["openssl"],
)

RSYNC = Package(
    name="rsync",
    version="3.3.0",
    url="https://download.samba.org/pub/rsync/src/rsync-3.3.0.tar.gz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="7399e9a6708c32d678a72a63219e96f23be0be2336e50fd1348498d07041df90",
        )
    ],
    configure_flags=["--disable-xxhash", "--disable-lz4", "--disable-zstd"],
    stage=3,
    depends=["openssl"],
)

# ---------------------------------------------------------------------------
# Master catalogue (build order within each stage is handled by graph.py)
# ---------------------------------------------------------------------------

#: All packages in catalogue order.
ALL_PACKAGES: list[Package] = [
    # Stage 1
    ZLIB,
    BZIP2,
    XZ,
    GZIP,
    LIBRESSL,
    MAKE,
    WGET,
    SED,
    PATCH,
    M4,
    BISON,
    GREP,
    COREUTILS,
    FINDUTILS,
    GAWK,
    TAR,
    BASH,
    LIBFFI,
    PYTHON,
    # Stage 2
    AUTOCONF,
    AUTOMAKE,
    LIBTOOL,
    PKG_CONFIG,
    BINUTILS,
    GCC,
    # Stage 3
    OPENSSL,
    CURL,
    RSYNC,
]

PACKAGES_BY_NAME: dict[str, Package] = {p.name: p for p in ALL_PACKAGES}

STAGE_PACKAGES: dict[int, list[Package]] = {
    1: [p for p in ALL_PACKAGES if p.stage == 1],
    2: [p for p in ALL_PACKAGES if p.stage == 2],
    3: [p for p in ALL_PACKAGES if p.stage == 3],
}

# GNU projects for which the mirror resolver can auto-detect latest versions.
# Non-GNU packages (libressl, openssl, curl, rsync, pkg-config, xz, zlib,
# bzip2, Python) and GitHub-hosted packages (libffi) are intentionally excluded.
GNU_PROJECTS: list[str] = [
    "autoconf",
    "automake",
    "bash",
    "binutils",
    "bison",
    "coreutils",
    "findutils",
    "gawk",
    "grep",
    "gzip",
    "libtool",
    "m4",
    "make",
    "patch",
    "sed",
    "tar",
    "wget",
]
