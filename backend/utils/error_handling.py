"""
Error handling utilities for the analysis pipeline.

Provides:
- Custom exception classes
- Error logging and tracking
- Graceful degradation strategies
- Retry logic
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class AnalysisException(Exception):
    """Base exception for analysis pipeline."""


class ValidationException(AnalysisException):
    """Raised when sequence validation fails."""


class AlignmentException(AnalysisException):
    """Raised when alignment fails."""


class MutationDetectionException(AnalysisException):
    """Raised when mutation detection fails."""


class AnnotationException(AnalysisException):
    """Raised when annotation fails."""


class ClassificationException(AnalysisException):
    """Raised when classification fails."""


class RetrievalException(AnalysisException):
    """Raised when clinical evidence retrieval fails."""


def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    timeout: int = 30,
    exceptions: tuple = (Exception,),
):
    """
    Decorator to retry a function on selected exceptions.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            wait_time = 1.0

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        logger.error(
                            "%s failed after %s attempts: %s",
                            func.__name__,
                            max_retries + 1,
                            str(exc),
                        )
                        raise

                    logger.warning(
                        "%s attempt %s failed: %s. Retrying in %ss...",
                        func.__name__,
                        attempt + 1,
                        str(exc),
                        wait_time,
                    )
                    time.sleep(wait_time)
                    wait_time = min(wait_time * backoff_factor, timeout)

            if last_exception is not None:
                raise last_exception

        return wrapper

    return decorator


class ErrorTracker:
    """Track errors and warnings during analysis."""

    def __init__(self) -> None:
        self.errors = []
        self.warnings = []
        self.logger = logging.getLogger("error_tracker")

    def add_error(self, error: str, exception: Optional[Exception] = None) -> None:
        """Record an error."""

        self.errors.append(error)
        self.logger.error(error)
        if exception is not None:
            self.logger.debug("Exception: %s", str(exception), exc_info=True)

    def add_warning(self, warning: str) -> None:
        """Record a warning."""

        self.warnings.append(warning)
        self.logger.warning(warning)

    def has_errors(self) -> bool:
        """Check whether any errors were recorded."""

        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check whether any warnings were recorded."""

        return len(self.warnings) > 0

    def get_summary(self) -> dict:
        """Return a summary dict of errors and warnings."""

        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def clear(self) -> None:
        """Clear all tracked issues."""

        self.errors.clear()
        self.warnings.clear()


class GracefulDegradation:
    """Strategies for graceful degradation when components fail."""

    @staticmethod
    def use_default_on_failure(default_value: Any, exceptions: tuple = (Exception,)):
        """
        Decorator to return a default value on failure.
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    logger.warning(
                        "%s failed, using default value: %s",
                        func.__name__,
                        str(exc),
                    )
                    return default_value

            return wrapper

        return decorator

    @staticmethod
    def skip_on_failure(exceptions: tuple = (Exception,)):
        """
        Decorator to skip an operation on failure.
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    logger.warning("%s skipped due to failure: %s", func.__name__, str(exc))
                    return None

            return wrapper

        return decorator


__all__ = [
    "AnalysisException",
    "ValidationException",
    "AlignmentException",
    "MutationDetectionException",
    "AnnotationException",
    "ClassificationException",
    "RetrievalException",
    "retry_on_exception",
    "ErrorTracker",
    "GracefulDegradation",
]
