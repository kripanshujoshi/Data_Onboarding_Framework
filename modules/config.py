"""
Configuration loader for Data Onboarding Framework.
"""
import logging
import json
import os

from modules.logging_setup import log_function

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'configs',
    'config.json'
)


@log_function
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


class ConfigManager:
    """
    Manages configuration with environment-specific overrides
    """

    def __init__(self):
        self.base_config = self._load_base_config()
        self.env_config = self._load_env_config()
        self.config = self._merge_configs()

    def _load_base_config(self):
        """Load the base configuration file"""
        with open('configs/config.json', 'r') as config_file:
            return json.load(config_file)

    def _load_env_config(self):
        """Load environment-specific configuration"""
        # Get environment from environment variable (set by Elastic Beanstalk)
        env = os.environ.get('DEPLOY_ENV', 'dev')

        # Check if we have an environment-specific config file
        env_config_path = f'configs/config-{env}.json'
        if os.path.exists(env_config_path):
            with open(env_config_path, 'r') as env_file:
                return json.load(env_file)
        return {}

    def _merge_configs(self):
        """Merge base and environment configs, with environment taking precedence"""
        merged = self.base_config.copy()

        # Replace top-level keys with environment values if they exist
        for key, value in self.env_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # If both are dicts, merge them
                merged[key] = {**merged[key], **value}
            else:
                # Otherwise replace the value
                merged[key] = value

        return merged

    def get_config(self):
        """Get the combined configuration"""
        return self.config


# Create a singleton instance
config_manager = ConfigManager()


def get_config():
    """
    Get configuration with environment variable overrides
    """
    # Load base configuration from file
    with open('configs/config.json', 'r') as config_file:
        config = json.load(config_file)
    
    # Override with environment variables if available
    env_vars = {
        'SECRETS_MANAGER_SECRET_NAME': 'secrets_manager_secret_name',
        'S3_BUCKET_NAME': 's3_bucket',
        'S3_ROOT_PREFIX': 's3_root_prefix',
        'DEPLOY_ENV': 'environment'
    }
    
    for env_var, config_key in env_vars.items():
        if env_var in os.environ:
            config[config_key] = os.environ[env_var]
    
    # Ensure environment is set (default to dev)
    if 'environment' not in config:
        config['environment'] = os.environ.get('DEPLOY_ENV', 'dev')
    
    return config
