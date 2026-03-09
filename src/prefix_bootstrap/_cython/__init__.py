"""
prefix_bootstrap._cython
~~~~~~~~~~~~~~~~~~~~~~~~

Cython extension package.

If the compiled ``.so`` is available, the fast C implementation is used.
Otherwise, a pure-Python fallback (``hasher_fallback``) is transparently
imported.  Application code should always import from
``prefix_bootstrap.hasher`` rather than from this sub-package directly.
"""
