"""
Mercury logging module.

This module provides consistent logging configuration across the Mercury platform.
"""

from ml.logging.config import configure_logging
from ml.logging.core import get_logger

# Configure logging when the module is imported
configure_logging()

__all__ = ["get_logger", "configure_logging"]

