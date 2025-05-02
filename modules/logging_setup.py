"""
Configure and initialize logging for the Data Onboarding Framework project.
"""
import logging
import os


def setup_logging():
    """
    Configure the root logger with a standard format and level from the LOG_LEVEL environment variable.
    Defaults to INFO level.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
