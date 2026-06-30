"""Unit tests for utils/logger.py."""
import logging

import pytest

from utils.logger import get_logger, setup_logging


def test_get_logger_returns_logger():
    log = get_logger("test.module")
    assert isinstance(log, logging.Logger)
    assert log.name == "test.module"


def test_setup_logging_sets_root_level():
    setup_logging(level="DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_setup_logging_default_level_is_info():
    setup_logging()
    assert logging.getLogger().level == logging.INFO


def test_setup_logging_warning_level():
    setup_logging(level="WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_setup_logging_adds_console_handler():
    setup_logging(level="INFO")
    root = logging.getLogger()
    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)


def test_setup_logging_with_log_file(tmp_path):
    log_file = str(tmp_path / "test.log")
    setup_logging(level="INFO", log_file=log_file)
    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) >= 1
    log = get_logger("file_test")
    log.info("test message")
    with open(log_file, encoding="utf-8") as f:
        content = f.read()
    assert "test message" in content


def test_setup_logging_clears_previous_handlers():
    setup_logging(level="INFO")
    initial_count = len(logging.getLogger().handlers)
    setup_logging(level="INFO")
    assert len(logging.getLogger().handlers) == initial_count
