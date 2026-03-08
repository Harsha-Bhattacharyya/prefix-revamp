# prefix-bootstrap

A modular, Cython-backed Python re-implementation of the
[Gentoo Prefix bootstrap script](https://wiki.gentoo.org/wiki/Prefix/Bootstrap),
targeting **Linux aarch64 (arm64)** with GNU utilities only.

macOS, BSD, and non-aarch64 architectures have been intentionally removed.
The tool uses modern Python libraries for every subsystem and enforces strict
formatting, linting, and type-checking.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Bootstrap](#running-the-bootstrap)
- [CLI Reference](#cli-reference)
- [Development](#development)
  - [Setup](#setup)
  - [Linting and Formatting](#linting-and-formatting)
  - [Type Checking](#type-checking)
  - [Running Tests](#running-tests)
  - [Building Cython Extensions](#building-cython-extensions)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Configuration Reference](#configuration-reference)
- [Adding a New Package](#adding-a-new-package)

---

## Features

- **Async downloads** via `aiohttp` with parallel fetching and rich progress bars.
- **Dependency graph** managed by `networkx` — packages are always built in
  safe topological order.
- **Pydantic-validated configuration** — every option is type-checked at
  startup; invalid values produce clear error messages.
- **Cython extension** (`_cython.hasher`) for fast SHA-256 / MD5 file
  verification; a pure-Python fallback is used when the extension has not been
  compiled.
- **Rich CLI output** via `rich` and `typer` — colour-coded status messages
  and download progress bars.
- **Structured logging** via `structlog` — human-readable in development, JSON
  in CI / production.
- **Build orchestration** via `plumbum` — subprocess calls are explicit,
  typed, and easy to test.
- **Three-stage bootstrap** mirrors the original shell script's phasing:
  - Stage 1: essential GNU userland (bash, coreutils, grep, sed, …)
  - Stage 2: build toolchain (m4, autoconf, binutils, GCC, …)
  - Stage 3: Portage prerequisites (openssl, curl, rsync)
- **Idempotent** — stamp files prevent re-building packages that are already
  installed. Safe to re-run after a failure.
- **GNU URL auto-resolution** — `prefix-bootstrap resolve` queries the
  configured GNU mirror and prints the latest version of every GNU package.

---

## Architecture

```
src/prefix_bootstrap/
  __init__.py          Package initialisation
  __main__.py          python -m prefix_bootstrap entry point
  __version__.py       Single-source version string
  cli.py               Typer CLI (run / download / show-deps / resolve / version)
  config.py            Pydantic BootstrapConfig model
  log.py               structlog configuration
  hasher.py            SHA-256 / MD5 helpers (Cython + pure-Python fallback)
  downloader.py        aiohttp async download engine
  extractor.py         tarfile extraction with path-safety checks
  builder.py           plumbum-backed configure / make / make install
  graph.py             networkx dependency graph + topological sort
  packages/
    __init__.py
    base.py            Package / Checksum pydantic models
    definitions.py     Catalogue of all bootstrap packages (versions + URLs)
    gnu.py             Async GNU mirror scraper (latest-version resolution)
  stages/
    __init__.py
    stage1.py          Stage 1 orchestrator (essential GNU tools)
    stage2.py          Stage 2 orchestrator (build toolchain)
    stage3.py          Stage 3 orchestrator (Portage prerequisites)
  _cython/
    __init__.py
    hasher.pyx         Cython SHA-256 / MD5 implementation
```

---

## Requirements

- Linux aarch64 (arm64) — x86-64 and other architectures are not supported.
- Python 3.11 or later.
- A working C compiler (for the Cython extension and the bootstrap itself).
- Internet access for downloading source tarballs (or pre-fetched tarballs in
  `--work-dir/distfiles`).

---

## Installation

### From source (recommended)

```bash
git clone https://github.com/Harsha-Bhattacharyya/prefix-revamp.git
cd prefix-revamp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Build the Cython extension (optional but recommended)

```bash
python setup.py build_ext --inplace
```

If Cython is not installed the pure-Python fallback is used automatically.

---

## Running the Bootstrap

```bash
# Full three-stage bootstrap to /usr/local/gentoo
prefix-bootstrap run --prefix /usr/local/gentoo

# Use a custom work directory (downloads + build trees)
prefix-bootstrap run \
    --prefix /usr/local/gentoo \
    --work-dir /mnt/fast/bootstrap

# Only run stages 1 and 2
prefix-bootstrap run --prefix /usr/local/gentoo --stages 1 --stages 2

# Increase download parallelism and verbosity
prefix-bootstrap run \
    --prefix /usr/local/gentoo \
    --log-level DEBUG

# Pre-download tarballs without building (useful for offline builds)
prefix-bootstrap download --prefix /usr/local/gentoo --work-dir /mnt/fast

# Use a specific GNU mirror
prefix-bootstrap run \
    --prefix /usr/local/gentoo \
    --mirror https://mirrors.kernel.org/gnu
```

The bootstrap is idempotent. If it fails part-way through, simply re-run the
same command; already-completed packages are detected via stamp files and
skipped. :)

---

## CLI Reference

```
Usage: prefix-bootstrap [OPTIONS] COMMAND [ARGS]...

Commands:
  run        Run the full Gentoo Prefix bootstrap (all stages, or a subset).
  download   Download tarballs only (no building).
  show-deps  Print the dependency tree and exit.
  resolve    Query GNU mirrors and print latest package versions.
  version    Print the tool version and exit.
```

### Common options (all commands except version / show-deps)

| Option | Default | Description |
|---|---|---|
| `--prefix / -p` | `/usr/local/gentoo` | Gentoo Prefix root ($EPREFIX) |
| `--work-dir / -w` | `$PREFIX/.bootstrap-work` | Scratch / build directory |
| `--stages / -s` | `1 2 3` | Bootstrap stages to execute |
| `--mirror` | `https://ftpmirror.gnu.org` | GNU FTP mirror base URL |
| `--log-level` | `INFO` | Logging verbosity |
| `--json-logs` | off | Emit newline-delimited JSON logs |
| `--skip-verify` | off | Skip checksum verification |

---

## Development

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Linting and Formatting

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Fix auto-fixable lint issues
ruff check --fix src tests
```

### Type Checking

```bash
mypy src
```

### Running Tests

```bash
pytest
```

To run without coverage (faster):

```bash
pytest --no-cov
```

To run a specific test module:

```bash
pytest tests/test_config.py -v
```

### Building Cython Extensions

```bash
python setup.py build_ext --inplace
```

---

## Project Structure

```
prefix-revamp/
  src/
    prefix_bootstrap/   Python package (see Architecture above)
  tests/                pytest test suite
  docs/                 Additional documentation
  pyproject.toml        Build system, dependencies, tool config
  setup.py              Cython extension build script
  README.md             This file
  LICENSE
```

---

## How It Works

The bootstrap proceeds in three stages, each building on the previous one.

### Stage 1 — Essential GNU userland

The system compiler builds a minimal set of GNU tools (bash, coreutils,
findutils, grep, sed, gawk, make, patch, tar, xz, bzip2, zlib) into a
temporary tools directory (`$WORK_DIR/tools`).  These tools replace any
possibly-ancient system tools for subsequent stages.

### Stage 2 — Build toolchain

Using the Stage 1 tools, the build toolchain is assembled: m4, autoconf,
automake, libtool, pkg-config, binutils, and GCC.  Outputs land in
`$EPREFIX/usr`.

### Stage 3 — Portage prerequisites

The networking stack needed to run `emerge` is built: openssl, curl, and
rsync.  After this stage the prefix is ready for `emerge --sync` and a
full Portage bootstrap.

---

## Configuration Reference

All options are modelled in `prefix_bootstrap.config.BootstrapConfig` using
Pydantic v2.  The model is frozen (immutable after construction) and every
field has a validator.

| Field | Type | Default | Description |
|---|---|---|---|
| `prefix` | `Path` | — | Gentoo Prefix root |
| `work_dir` | `Path` | — | Scratch directory |
| `arch` | `str` | `aarch64` | CPU architecture (read-only) |
| `chost` | `str` | auto | GNU host triplet |
| `gnu_mirror` | `str` | `https://ftpmirror.gnu.org` | GNU mirror |
| `parallel_downloads` | `int` | 4 | Concurrent downloads (1-32) |
| `retries` | `int` | 3 | Download retry count (0-10) |
| `log_level` | `str` | `INFO` | Python log level |
| `json_logs` | `bool` | `False` | JSON log output |
| `skip_verify` | `bool` | `False` | Skip checksums |
| `stages` | `list[int]` | `[1, 2, 3]` | Stages to run |

---

## Adding a New Package

1. Add a `Package` instance to `src/prefix_bootstrap/packages/definitions.py`,
   setting the correct `stage` and `depends` fields.
2. Append the instance to `ALL_PACKAGES` at the bottom of the file.
3. Run `pytest tests/test_packages.py` to verify the catalogue is consistent.
4. Run `pytest` for the full test suite.

The dependency graph is built automatically from the `depends` field; the
topological sort ensures the new package is built after all its dependencies
without any manual ordering. :D
