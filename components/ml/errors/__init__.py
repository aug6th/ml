"""
ML Error Handling

This package provides standardized error handling for ML components,
including custom exception types, error codes, and utility functions.
"""

from ml.errors.errors import (
    APIError,
    ClassificationError,
    ConnectionError,
    ErrorCode,
    MLError,
    ScrapingError,
    collect_validation_errors,
    format_error_for_response,
)

__all__ = [
    "APIError",
    "ClassificationError",
    "ConnectionError",
    "ErrorCode",
    "MLError",
    "ScrapingError",
    "collect_validation_errors",
    "format_error_for_response",
]
