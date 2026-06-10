"""Logging setup for xa_dose_analysis.

The package logs progress and diagnostics through the standard :mod:`logging`
module instead of printing. Call :func:`setup_logging` once at the top of a
notebook or script to see the messages:

    import xa_dose_analysis as xa
    xa.setup_logging("INFO")    # "DEBUG" for more detail, "WARNING" for less
"""

import logging
import sys
from pathlib import Path

PACKAGE_LOGGER_NAME = "xa_dose_analysis"


def setup_logging(level: int | str = "INFO", log_file: str | Path | None = None) -> logging.Logger:
    """Configure logging output for the package.

    Parameters
    ----------
    level:
        Logging level, e.g. "DEBUG", "INFO" or "WARNING".
    log_file:
        Optional path; if given, messages are also appended to this file.

    Returns
    -------
    The package logger.
    """
    logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    logger.setLevel(level)

    # Replace existing handlers so repeated calls (common in notebooks) do not
    # produce duplicated messages.
    logger.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(stream_handler)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Return a child logger for a module, e.g. ``get_logger(__name__)``."""
    return logging.getLogger(module_name)
