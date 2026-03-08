"""
prefix_bootstrap.__main__
~~~~~~~~~~~~~~~~~~~~~~~~~

Entry point — allows ``python -m prefix_bootstrap`` as well as the
``prefix-bootstrap`` console-script.

When run without any subcommand (i.e. just ``python -m prefix_bootstrap`` or
``prefix-bootstrap``), the interactive TUI is launched — exactly as the
original ``bootstrap-prefix.sh`` does when invoked without arguments.  :D
"""

import sys

from prefix_bootstrap.cli import app

if __name__ == "__main__":
    # If no subcommand was given, launch the TUI (original interactive mode).
    if len(sys.argv) == 1:
        from prefix_bootstrap.tui import run_tui

        run_tui()
    else:
        app()
