"""
setup.py — build Cython extensions for prefix-bootstrap.

The ``prefix_bootstrap._cython.hasher`` extension provides a fast
SHA-256 / MD5 digest helper that is used during tarball verification.
Pure-Python fallback is available if Cython is not installed.
"""

from __future__ import annotations

from setuptools import Extension, setup

try:
    from Cython.Build import cythonize  # type: ignore[import-untyped]

    extensions = cythonize(
        [
            Extension(
                "prefix_bootstrap._cython.hasher",
                sources=["src/prefix_bootstrap/_cython/hasher.pyx"],
                extra_compile_args=["-O3"],
            )
        ],
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
        },
    )
except ImportError:
    # Cython is not available at build time; fall back to the pure-Python shim.
    extensions = []

setup(ext_modules=extensions)
