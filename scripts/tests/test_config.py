"""Tests for configuration module."""

import os
from unittest import mock

import pytest

from config import Config, GristConfig, get_config


class TestConfig:
    """Test configuration management."""

    def test_default_environment(self):
        """Test that default environment is dev."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Reload to get fresh instance
            from config import Config
            assert Config.ENVIRONMENT == "dev"

    def test_is_dev(self):
        """Test is_dev check."""
        with mock.patch.dict(os.environ, {"ENVIRONMENT": "dev"}):
            from config import Config
            assert Config.is_dev() is True
            assert Config.is_test() is False
            assert Config.is_production() is False

    def test_is_test(self):
        """Test is_test check."""
        with mock.patch.dict(os.environ, {"ENVIRONMENT": "test"}):
            from config import Config
            assert Config.is_test() is True
            assert Config.is_dev() is False
            assert Config.is_production() is False

    def test_is_production(self):
        """Test is_production check."""
        with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            from config import Config
            assert Config.is_production() is True
            assert Config.is_dev() is False
            assert Config.is_test() is False

    def test_prod_alias(self):
        """Test that 'prod' is recognized as production."""
        with mock.patch.dict(os.environ, {"ENVIRONMENT": "prod"}):
            from config import Config
            assert Config.is_production() is True


class TestGristConfig:
    """Test Grist configuration."""

    def test_dev_config(self):
        """Test dev environment config."""
        env_vars = {
            "ENVIRONMENT": "dev",
            "GRIST_URL": "http://dev:8484",
            "GRIST_API_KEY": "dev_key",
            "GRIST_DOC_ID": "dev_doc",
        }
        with mock.patch.dict(os.environ, env_vars, clear=True):
            config = get_config()
            assert config.url == "http://dev:8484"
            assert config.api_key == "dev_key"
            assert config.doc_id == "dev_doc"

    def test_test_config(self):
        """Test test environment config."""
        env_vars = {
            "ENVIRONMENT": "dev",  # Current env
            "TEST_GRIST_URL": "http://test:8485",
            "TEST_GRIST_API_KEY": "test_key",
            "TEST_GRIST_DOC_ID": "test_doc",
        }
        with mock.patch.dict(os.environ, env_vars, clear=True):
            config = get_config("test")  # Override to test
            assert config.url == "http://test:8485"
            assert config.api_key == "test_key"
            assert config.doc_id == "test_doc"

    def test_production_config(self):
        """Test production environment config."""
        env_vars = {
            "ENVIRONMENT": "dev",
            "PROD_GRIST_URL": "http://prod:8484",
            "PROD_GRIST_API_KEY": "prod_key",
            "PROD_GRIST_DOC_ID": "prod_doc",
        }
        with mock.patch.dict(os.environ, env_vars, clear=True):
            config = get_config("production")
            assert config.url == "http://prod:8484"
            assert config.api_key == "prod_key"
            assert config.doc_id == "prod_doc"

    def test_default_urls(self):
        """Test default URLs when not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = get_config("dev")
            assert config.url == "http://localhost:8484"
            
            config = get_config("test")
            assert config.url == "http://localhost:8485"
            
            config = get_config("production")
            assert config.url == "http://localhost:8484"

    def test_config_override(self):
        """Test that explicit env parameter overrides ENVIRONMENT."""
        env_vars = {
            "ENVIRONMENT": "production",
            "TEST_GRIST_URL": "http://test-override:8485",
            "TEST_GRIST_API_KEY": "test_key",
            "TEST_GRIST_DOC_ID": "test_doc",
        }
        with mock.patch.dict(os.environ, env_vars, clear=True):
            # Even though ENVIRONMENT=production, we request test
            config = get_config("test")
            assert config.url == "http://test-override:8485"
