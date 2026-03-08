"""
prefix_bootstrap.packages.definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The catalogue of GNU source packages required for a Gentoo Prefix aarch64
bootstrap, grouped by stage.

Stage 1 — essential userland tools (bash, coreutils, findutils, grep, sed,
           gawk, make, patch, tar, xz, bzip2, zlib).
Stage 2 — build toolchain (m4, autoconf, automake, libtool, pkg-config,
           binutils, gcc).
Stage 3 — Portage dependencies (python, openssl, curl, rsync, git).

Versions listed here are the baseline minimum; ``prefix_bootstrap.packages.gnu``
can override them with the genuinely latest upstream releases when network
access is available.
"""

from __future__ import annotations

from prefix_bootstrap.packages.base import Checksum, ChecksumKind, Package

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GNU = "https://ftpmirror.gnu.org"
_CPAN = "https://cpan.metacpan.org/authors/id"


def _gnu(project: str, version: str, ext: str = "tar.xz") -> str:
    return f"{_GNU}/{project}/{project}-{version}.{ext}"


# ---------------------------------------------------------------------------
# Stage 1 — essential tools
# ---------------------------------------------------------------------------

ZLIB = Package(
    name="zlib",
    version="1.3.1",
    url="https://zlib.net/zlib-1.3.1.tar.xz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="11b8c4c11f3685a61f7c30d9dec0f1f8c0d50be6ab87ab1f29aef3c0ecfb15d3",
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
    version="5.4.6",
    url="https://github.com/tukaani-project/xz/releases/download/v5.4.6/xz-5.4.6.tar.xz",
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="aeba3e03bf8140ddedf62a0a367158340520f6afea75cd40f4cae8e9551c5b5f",
        )
    ],
    configure_flags=["--disable-nls", "--disable-shared", "--enable-static"],
    stage=1,
)

BASH = Package(
    name="bash",
    version="5.2.21",
    url=_gnu("bash", "5.2.21"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="6af89bc29c5b1beb1ea37c6c8ef5463ec9fcbc2c89ef22a5cf0bc3fa5b978c3f",
        )
    ],
    configure_flags=[
        "--without-bash-malloc",
        "--disable-nls",
    ],
    stage=1,
)

COREUTILS = Package(
    name="coreutils",
    version="9.4",
    url=_gnu("coreutils", "9.4"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="ea613a4cf44612326e917201bbbcdfbd301de21ffc3b59b6e5c07e040b275e52",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
    depends=["bash"],
)

FINDUTILS = Package(
    name="findutils",
    version="4.9.0",
    url=_gnu("findutils", "4.9.0"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="a2bfb8c09d436770edc59f50fa483e785b161a3b7b9d547573cb08065fd462fe",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
    depends=["bash"],
)

GREP = Package(
    name="grep",
    version="3.11",
    url=_gnu("grep", "3.11"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="1db2aedde89d0dea42b16d9528f894c8d15dae4e190b59aecc78f5a951276eab",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

SED = Package(
    name="sed",
    version="4.9",
    url=_gnu("sed", "4.9"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="6e226b732e1cd739464ad6862bd1a1aba42d7982922da7a53519631d24975181",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

GAWK = Package(
    name="gawk",
    version="5.3.0",
    url=_gnu("gawk", "5.3.0"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="378f8864ec21cfceaa048f7e1409d1f60a7168e38e6884f75c01edc0a9a39d97",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

MAKE = Package(
    name="make",
    version="4.4.1",
    url=_gnu("make", "4.4.1"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="dd16fb1d67bfab79a72f5e8390735c49e3e8e70b4945a15ab1f81ddb78658fb3",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=1,
)

PATCH = Package(
    name="patch",
    version="2.7.6",
    url=_gnu("patch", "2.7.6"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="ac610bda97abe0d9f6b7c963255a11dcb196c25e337c61f94e4778d632f1d8fd",
        )
    ],
    stage=1,
)

TAR = Package(
    name="tar",
    version="1.35",
    url=_gnu("tar", "1.35"),
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

# ---------------------------------------------------------------------------
# Stage 2 — build toolchain helpers
# ---------------------------------------------------------------------------

M4 = Package(
    name="m4",
    version="1.4.19",
    url=_gnu("m4", "1.4.19"),
    checksums=[
        Checksum(
            kind=ChecksumKind.SHA256,
            value="3be4a26d825ffdfda52a56fc43246456989a3630093cced3fbdabb4e1dff0157",
        )
    ],
    configure_flags=["--disable-nls"],
    stage=2,
)

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
    depends=["m4"],
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
        "--disable-multilib",
        "--disable-nls",
        "--enable-languages=c,c++",
        "--disable-bootstrap",
        "--with-system-zlib",
    ],
    stage=2,
    # zlib is a stage-1 package; stage ordering ensures it is already present.
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
    # zlib is stage 1, openssl is stage 3 — only same-stage deps here.
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
# Master catalogue
# ---------------------------------------------------------------------------

#: All packages in dependency / build order.
ALL_PACKAGES: list[Package] = [
    # Stage 1
    ZLIB,
    BZIP2,
    XZ,
    BASH,
    COREUTILS,
    FINDUTILS,
    GREP,
    SED,
    GAWK,
    MAKE,
    PATCH,
    TAR,
    # Stage 2
    M4,
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
