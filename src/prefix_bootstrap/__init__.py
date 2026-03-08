"""
prefix_bootstrap
~~~~~~~~~~~~~~~~

A modular, Cython-backed Python re-implementation of the Gentoo Prefix
bootstrap script, targeting **Linux aarch64 (arm64)** with GNU utilities.

Quickstart::

    prefix-bootstrap --prefix /usr/local/gentoo run

See ``prefix-bootstrap --help`` for the full option list.
"""

from prefix_bootstrap.__version__ import __version__

__all__ = ["__version__"]
