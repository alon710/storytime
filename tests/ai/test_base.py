"""Unit tests for the base AI module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.genai import types
from jinja2 import Environment

from app.ai.base import BaseAIGenerator


class ConcreteAIGenerator(BaseAIGenerator):
    """Concrete implementation for testing."""

    def generate(self, *args, **kwargs):
        return "generated content"


class TestBaseAIGenerator:
    """Test BaseAIGenerator abstract class."""

    def test_initialization(self, mock_genai_client):
        """Test BaseAIGenerator initialization."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        assert generator.client == mock_genai_client
        assert generator.model == "test-model"
        assert isinstance(generator.env, Environment)

    def test_template_directory_setup(self, mock_genai_client):
        """Test that template directory is correctly set up."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        # Check that the template loader is configured
        assert generator.env.loader is not None

        # Verify the template directory path
        Path(__file__).parent.parent.parent / "app" / "ai" / "templates"
        loader_path = Path(generator.env.loader.searchpath[0])  # type: ignore[attr-defined]
        assert loader_path.name == "templates"

    def test_generate_content_success(self, mock_genai_client):
        """Test successful content generation."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        # Mock response
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = "Generated text"
        mock_genai_client.models.generate_content.return_value = mock_response

        result = generator._generate_content(
            contents=["Test prompt"],
            response_modalities=["text"],
        )

        assert result == mock_response
        mock_genai_client.models.generate_content.assert_called_once()

    def test_generate_content_with_config(self, mock_genai_client):
        """Test content generation with custom config."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_genai_client.models.generate_content.return_value = mock_response

        custom_config = types.GenerateContentConfig(
            temperature=0.5,
            top_p=0.9,
        )

        result = generator._generate_content(
            contents=["Test prompt"],
            config=custom_config,
        )

        assert result == mock_response

        # Verify the config was passed
        call_args = mock_genai_client.models.generate_content.call_args
        assert call_args.kwargs["config"] == custom_config

    def test_generate_content_no_response(self, mock_genai_client):
        """Test handling of no response from API."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        mock_genai_client.models.generate_content.return_value = None

        result = generator._generate_content(contents=["Test prompt"])

        assert result is None

    def test_generate_content_no_candidates(self, mock_genai_client):
        """Test handling of response with no candidates."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        mock_response = MagicMock()
        mock_response.candidates = []
        mock_genai_client.models.generate_content.return_value = mock_response

        result = generator._generate_content(contents=["Test prompt"])

        assert result is None

    def test_generate_content_empty_candidates(self, mock_genai_client):
        """Test handling of response with None candidates."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        mock_response = MagicMock()
        mock_response.candidates = None
        mock_genai_client.models.generate_content.return_value = mock_response

        result = generator._generate_content(contents=["Test prompt"])

        assert result is None

    def test_abstract_generate_method(self, mock_genai_client):
        """Test that generate method must be implemented."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            BaseAIGenerator(mock_genai_client, "test-model")

    def test_generate_content_with_response_modalities(self, mock_genai_client):
        """Test content generation with response modalities."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_genai_client.models.generate_content.return_value = mock_response

        result = generator._generate_content(
            contents=["Test prompt"],
            response_modalities=["text", "image"],
        )

        assert result == mock_response

        # Verify the response modalities were set in config
        call_args = mock_genai_client.models.generate_content.call_args
        config = call_args.kwargs["config"]
        assert config.response_modalities == ["text", "image"]

    @patch("app.ai.base.logger")
    def test_generate_content_logs_warning(self, mock_logger, mock_genai_client):
        """Test that warning is logged when no response."""
        generator = ConcreteAIGenerator(mock_genai_client, "test-model")

        mock_genai_client.models.generate_content.return_value = None

        generator._generate_content(contents=["Test prompt"])

        mock_logger.warning.assert_called_once_with(
            "No response received from Gemini API",
            classname="ConcreteAIGenerator",
        )