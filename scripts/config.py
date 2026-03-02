"""Configuration management for Grist Stock Tracker.

Supports multiple environments: dev, test, production.
Environment is determined by the ENVIRONMENT variable (default: dev).
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class GristConfig:
    """Grist configuration for a specific environment."""

    url: str
    api_key: str
    doc_id: str


class Config:
    """Application configuration manager."""

    @classmethod
    def _get_env(cls) -> str:
        """Get current environment from ENVIRONMENT variable."""
        return os.getenv("ENVIRONMENT", "dev")

    @classmethod
    @property
    def ENVIRONMENT(cls) -> str:
        """Current environment name."""
        return cls._get_env()

    @classmethod
    def get_grist_config(cls, override_env: Optional[str] = None) -> GristConfig:
        """Get Grist configuration for the specified or current environment.

        Args:
            override_env: Optional environment override ('test', 'prod', 'dev')

        Returns:
            GristConfig instance with environment-specific settings
        """
        env = override_env or cls._get_env()

        if env == "test":
            return GristConfig(
                url=os.getenv("TEST_GRIST_URL", "http://localhost:8485").rstrip('/'),
                api_key=os.getenv("TEST_GRIST_API_KEY", ""),
                doc_id=os.getenv("TEST_GRIST_DOC_ID", ""),
            )
        elif env == "production" or env == "prod":
            return GristConfig(
                url=os.getenv("PROD_GRIST_URL", "http://localhost:8484").rstrip('/'),
                api_key=os.getenv("PROD_GRIST_API_KEY", ""),
                doc_id=os.getenv("PROD_GRIST_DOC_ID", ""),
            )
        else:  # dev (default)
            return GristConfig(
                url=os.getenv("GRIST_URL", "http://localhost:8484").rstrip('/'),
                api_key=os.getenv("GRIST_API_KEY", ""),
                doc_id=os.getenv("GRIST_DOC_ID", ""),
            )

    @classmethod
    def is_test(cls) -> bool:
        """Check if running in test environment."""
        return cls._get_env() == "test"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls._get_env() in ("production", "prod")

    @classmethod
    def is_dev(cls) -> bool:
        """Check if running in dev environment."""
        return cls._get_env() in ("dev", "development")


# Convenience function for getting config
def get_config(env: Optional[str] = None) -> GristConfig:
    """Get configuration for specified environment."""
    return Config.get_grist_config(env)
