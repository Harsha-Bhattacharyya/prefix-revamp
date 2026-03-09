"""
prefix_bootstrap.stages
~~~~~~~~~~~~~~~~~~~~~~~~

Bootstrap stage orchestrators.

Each stage function follows the same pattern:

1. Collect the packages for this stage.
2. Sort them topologically.
3. Download missing tarballs.
4. Extract, configure, compile, and install each package.
"""
