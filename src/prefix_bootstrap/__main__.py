"""
prefix_bootstrap.__main__
~~~~~~~~~~~~~~~~~~~~~~~~~

Entry point — allows ``python -m prefix_bootstrap`` as well as the
``prefix-bootstrap`` console-script.
"""

from prefix_bootstrap.cli import app

if __name__ == "__main__":
    app()
