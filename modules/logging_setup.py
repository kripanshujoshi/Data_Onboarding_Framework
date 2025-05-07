"""
Configure and initialize logging for the Data Onboarding Framework project.
"""
import logging
import os
import functools


def setup_logging():
    """
    Configure the root logger with a standard format and level from the LOG_LEVEL environment variable.
    Defaults to INFO level. Optionally logs to a file if LOG_FILE environment variable is set.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_handlers = [logging.StreamHandler()]
    log_file = os.getenv("LOG_FILE")
    if log_file:
        try:
            log_handlers.append(logging.FileHandler(log_file))
        except Exception as e:
            print(f"Failed to set up file logging: {e}")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=log_handlers
    )


def log_function(func):
    """Decorator to log function entry, exit, and exceptions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Entering {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__}")
            return result
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {e}")
            raise
    return wrapper
