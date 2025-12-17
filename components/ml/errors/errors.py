"""
Standardized error handling for ML components

This module provides a consistent error handling system for ML components,
including custom exception types, error codes, and utility functions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorCode(Enum):
    """Error codes for ML components"""

    UNKNOWN = "unknown"
    INVALID_ARGUMENT = "invalid_argument"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    CONNECTION_ERROR = "connection_error"
    API_ERROR = "api_error"
    SCRAPING_ERROR = "scraping_error"
    CLASSIFICATION_ERROR = "classification_error"


class MLError(Exception):
    """Base exception for all ML errors"""

    def __init__(
        self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None
    ):
        """
        Initialize an ML error

        Args:
            code: Error code
            message: Error message
            details: Additional error details
            cause: Original exception that caused this error
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.cause = cause

        full_message = f"{code.value}: {message}"
        if cause:
            full_message += f" (caused by: {str(cause)})"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation"""
        result = {
            "code": self.code.value,
            "message": self.message,
        }

        if self.details:
            result["details"] = self.details

        if self.cause:
            result["cause"] = str(self.cause)

        return result


class ConnectionError(MLError):
    """Error related to connection handling"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(ErrorCode.CONNECTION_ERROR, message, details, cause)


class APIError(MLError):
    """Error related to API operations"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(ErrorCode.API_ERROR, message, details, cause)


class ScrapingError(MLError):
    """Error related to scraping operations"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(ErrorCode.SCRAPING_ERROR, message, details, cause)


class ClassificationError(MLError):
    """Error related to classification operations"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(ErrorCode.CLASSIFICATION_ERROR, message, details, cause)


def format_error_for_response(error: Exception) -> Dict[str, Any]:
    """
    Format an exception for API response

    Args:
        error: Exception to format

    Returns:
        Dictionary with error details suitable for API response
    """
    if isinstance(error, MLError):
        return error.to_dict()
    else:
        return {
            "code": ErrorCode.UNKNOWN.value,
            "message": str(error),
        }


def collect_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Collect validation errors into a standardized format

    Args:
        errors: List of validation errors

    Returns:
        Dictionary with validation errors in a standardized format
    """
    return {
        "code": ErrorCode.INVALID_ARGUMENT.value,
        "message": "Validation error",
        "details": {"validation_errors": errors},
    }
