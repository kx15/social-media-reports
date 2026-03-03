"""Shared utilities: exponential-backoff decorator and logging helper."""
from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def get_logger(name: str) -> logging.Logger:
    """Return a logger with a consistent format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator: retry *fn* up to *max_retries* times with exponential back-off."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(fn.__module__)
            delay = base_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_retries:
                        logger.error(
                            "%s failed after %d attempts: %s", fn.__name__, max_retries, exc
                        )
                        raise
                    logger.warning(
                        "%s attempt %d/%d failed (%s). Retrying in %.1fs…",
                        fn.__name__,
                        attempt,
                        max_retries,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

        return wrapper  # type: ignore[return-value]

    return decorator
