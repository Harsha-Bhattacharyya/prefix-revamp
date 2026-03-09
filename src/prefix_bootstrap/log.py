"""
prefix_bootstrap.log
~~~~~~~~~~~~~~~~~~~~~

Centralised structlog configuration.

Call ``configure_logging(level, json)`` once at programme start.  After that
all modules can do::

    import structlog
    log = structlog.get_logger(__name__)
    log.info("hello", key="value")

No emojis are used in log messages — they belong in CLI output only.
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", *, json_output: bool = False) -> None:
    """Initialise structlog with the requested verbosity and format.

    Parameters
    ----------
    level:
        Standard Python log level name (``DEBUG``, ``INFO``, ``WARNING`` …).
    json_output:
        When *True*, emit newline-delimited JSON instead of human-readable
        console output.  Useful for log aggregation pipelines.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
