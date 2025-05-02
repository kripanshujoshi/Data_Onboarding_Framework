"""
Configuration loader for Data Onboarding Framework.
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs', 'config.json')


def load_config():
    """
    Load and return the application configuration from JSON file.
    Raises an exception if file missing or invalid.
    """
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        logger.info(f"Configuration loaded from {CONFIG_PATH}")
        return cfg
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

# Load once at import
config = load_config()