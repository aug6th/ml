"""
Logging configuration.

This module provides centralized logging configuration for the Mercury platform.
"""

import logging
import os

fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"

log_level_map = {"1": logging.DEBUG, "2": logging.INFO, "3": logging.WARNING, "4": logging.ERROR}

default_log_level = logging.INFO
log_level = os.environ.get("LOG_LEVEL", default_log_level)
if isinstance(log_level, str) and log_level in log_level_map:
    log_level = log_level_map.get(log_level, default_log_level)


def configure_logging():
    """Configure root logger with consistent formatting."""
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(log_level)

