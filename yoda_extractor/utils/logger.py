"""
Centralised logging configuration for the Yoda Extractor.

Usage in any module:
    from utils.logger import get_logger
    log = get_logger(__name__)

Call setup_logging() once at startup (done in main.py).
Default level is INFO; use --log-level DEBUG to see LLM prompts and responses.
"""

import logging
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT = "%H:%M:%S"

_configured = False


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """Configure root logger. Call once from main.py."""
    global _configured
    numeric = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(numeric)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(console)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(numeric)
        fh.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        root.addHandler(fh)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger. setup_logging() need not have been called yet."""
    return logging.getLogger(name)
