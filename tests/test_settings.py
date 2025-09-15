"""Unit tests for the settings module."""

import os
from unittest.mock import patch


from app.utils.settings import Settings


class TestSettings:
    """Test Settings configuration."""

    def test_settings_default_values(self):
        """Test Settings with default values."""
        # Need to also patch the .env file loading
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.utils.settings.Settings.model_config", {"env_file": None}):
                test_settings = Settings()
                assert test_settings.google_api_key == ""
                assert test_settings.model == "gemini-2.5-flash-image-preview"
                assert test_settings.log_level == "INFO"

    def test_settings_from_environment(self):
        """Test Settings loading from environment variables."""
        env_vars = {
            "GOOGLE_API_KEY": "test-api-key-123",
            "MODEL": "custom-model",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.google_api_key == "test-api-key-123"
            assert test_settings.model == "custom-model"
            assert test_settings.log_level == "DEBUG"

    def test_settings_partial_environment(self):
        """Test Settings with partial environment variables."""
        env_vars = {
            "GOOGLE_API_KEY": "partial-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("app.utils.settings.Settings.model_config", {"env_file": None}):
                test_settings = Settings()
                assert test_settings.google_api_key == "partial-key"
                assert test_settings.model == "gemini-2.5-flash-image-preview"  # Default
                assert test_settings.log_level == "INFO"  # Default

    def test_settings_model_config(self):
        """Test Settings model configuration."""
        assert Settings.model_config["env_file"] == ".env"
        assert Settings.model_config["env_file_encoding"] == "utf-8"

    @patch("app.utils.settings.Settings")
    def test_settings_singleton(self, mock_settings_class):
        """Test that settings is a singleton instance."""
        # Import should create a single instance
        from app.utils.settings import settings as imported_settings

        assert imported_settings is not None

    def test_settings_field_types(self):
        """Test that settings fields have correct types."""
        test_settings = Settings()
        assert isinstance(test_settings.google_api_key, str)
        assert isinstance(test_settings.model, str)
        assert isinstance(test_settings.log_level, str)

    def test_settings_case_sensitivity(self):
        """Test that environment variable names are case-sensitive."""
        env_vars = {
            "google_api_key": "lowercase-key",  # Wrong case
            "GOOGLE_API_KEY": "correct-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.google_api_key == "correct-key"

    def test_settings_empty_string_values(self):
        """Test Settings with empty string environment values."""
        env_vars = {
            "GOOGLE_API_KEY": "",
            "MODEL": "",
            "LOG_LEVEL": "",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.google_api_key == ""
            assert test_settings.model == ""
            assert test_settings.log_level == ""