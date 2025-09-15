"""Integration tests for the TextProcessor module."""

import json
from unittest.mock import MagicMock, patch


from app.ai.text_processor import TextProcessor
from app.utils.schemas import Gender, Language, PageData, StoryMetadata


class TestTextProcessor:
    """Test TextProcessor class."""

    def test_initialization(self, mock_genai_client):
        """Test TextProcessor initialization."""
        processor = TextProcessor(mock_genai_client, "test-model")

        assert processor.client == mock_genai_client
        assert processor.model == "test-model"
        assert processor.env is not None

    def test_generate_method_delegates_to_process_pages(self, mock_genai_client):
        """Test that generate method delegates to process_pages."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text 1",
                illustration_prompt="Prompt 1",
            )
        ]
        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
        )

        with patch.object(processor, "process_pages") as mock_process:
            mock_process.return_value = {0: "Processed text"}
            result = processor.generate(pages=pages, metadata=metadata)

        assert result == {0: "Processed text"}
        mock_process.assert_called_once_with(pages=pages, metadata=metadata)

    def test_process_pages_success(self, mock_genai_client, sample_metadata):
        """Test successful page processing."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="The Beginning",
                story_text="Once upon a time, {character_name} was happy.",
                illustration_prompt="Happy child",
            ),
            PageData(
                title="The Journey",
                story_text="{character_name} went on an adventure.",
                illustration_prompt="Adventure scene",
            ),
        ]

        # Mock the API response with JSON - need to mock the direct client call
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = json.dumps(
            {
                "pages": [
                    {"page_index": 0, "personalized_text": "Once upon a time, Alice was happy."},
                    {"page_index": 1, "personalized_text": "Alice went on an adventure."},
                ]
            }
        )
        # The processor calls the client directly, not through _generate_content
        # Mock the actual response structure expected by the implementation
        mock_response.candidates[0].content.parts[0].text = json.dumps(
            {
                "personalized_pages": [
                    {"page_number": 1, "personalized_text": "Once upon a time, Alice was happy."},
                    {"page_number": 2, "personalized_text": "Alice went on an adventure."},
                ]
            }
        )
        processor.client.models.generate_content.return_value = mock_response

        result = processor.process_pages(pages=pages, metadata=sample_metadata)

        assert result == {
            0: "Once upon a time, Alice was happy.",
            1: "Alice went on an adventure.",
        }

    def test_process_pages_with_language(self, mock_genai_client):
        """Test page processing with different language."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="The Beginning",
                story_text="Hello {character_name}",
                illustration_prompt="Greeting",
            )
        ]

        metadata = StoryMetadata(
            character_name="David",
            age=8,
            gender=Gender.boy,
            language=Language.hebrew,
        )

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = json.dumps(
            {"personalized_pages": [{"page_number": 1, "personalized_text": "שלום דוד"}]}
        )
        processor.client.models.generate_content.return_value = mock_response

        result = processor.process_pages(pages=pages, metadata=metadata)

        assert result == {0: "שלום דוד"}

        # Verify the language was passed in the prompt
        call_args = processor.client.models.generate_content.call_args
        prompt = call_args.kwargs["contents"][0]
        assert "Hebrew" in prompt

    def test_process_pages_invalid_json_response(self, mock_genai_client, sample_metadata):
        """Test handling of invalid JSON response."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text 1",
                illustration_prompt="Prompt 1",
            )
        ]

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = "Invalid JSON"
        mock_genai_client.models.generate_content.return_value = mock_response

        result = processor.process_pages(pages=pages, metadata=sample_metadata)

        assert result == {}

    def test_process_pages_missing_pages_key(self, mock_genai_client, sample_metadata):
        """Test handling of response without 'pages' key."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text 1",
                illustration_prompt="Prompt 1",
            )
        ]

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = json.dumps({"other_key": "value"})
        mock_genai_client.models.generate_content.return_value = mock_response

        result = processor.process_pages(pages=pages, metadata=sample_metadata)

        assert result == {}

    def test_process_pages_no_response(self, mock_genai_client, sample_metadata):
        """Test handling of no API response."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text 1",
                illustration_prompt="Prompt 1",
            )
        ]

        mock_genai_client.models.generate_content.return_value = None

        result = processor.process_pages(pages=pages, metadata=sample_metadata)

        assert result == {}

    def test_process_pages_exception_handling(self, mock_genai_client, sample_metadata):
        """Test exception handling during page processing."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text 1",
                illustration_prompt="Prompt 1",
            )
        ]

        mock_genai_client.models.generate_content.side_effect = Exception("API Error")

        result = processor.process_pages(pages=pages, metadata=sample_metadata)

        assert result == {}

    def test_process_pages_with_instructions(self, mock_genai_client):
        """Test page processing with custom instructions."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text with {character_name}",
                illustration_prompt="Prompt 1",
            )
        ]

        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
            instructions="Make it very magical and whimsical",
        )

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = json.dumps(
            {"personalized_pages": [{"page_number": 1, "personalized_text": "Magical text with Alice"}]}
        )
        processor.client.models.generate_content.return_value = mock_response

        result = processor.process_pages(pages=pages, metadata=metadata)

        assert result == {0: "Magical text with Alice"}

        # Verify instructions were included in the prompt
        call_args = processor.client.models.generate_content.call_args
        prompt = call_args.kwargs["contents"][0]
        assert "magical and whimsical" in prompt

    def test_process_pages_template_rendering(self, mock_genai_client, sample_metadata):
        """Test that the Jinja2 template is properly rendered."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Story text",
                illustration_prompt="Prompt",
            )
        ]

        # Mock template rendering
        with patch.object(processor.env, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "Rendered prompt"
            mock_get_template.return_value = mock_template

            mock_response = MagicMock()
            mock_response.candidates = [MagicMock()]
            mock_response.candidates[0].content.parts = [MagicMock()]
            mock_response.candidates[0].content.parts[0].text = json.dumps(
                {"pages": [{"page_index": 0, "personalized_text": "Processed"}]}
            )
            processor.client.models.generate_content.return_value = mock_response

            processor.process_pages(pages=pages, metadata=sample_metadata)

        mock_get_template.assert_called_once_with("text_personalization.j2")
        mock_template.render.assert_called_once()

        # Verify template parameters
        render_args = mock_template.render.call_args.kwargs
        assert render_args["character_name"] == "Alice"
        assert render_args["character_age"] == 7
        assert render_args["character_gender"] == "Girl"  # Correct parameter name
        assert render_args["language"] == "English"
        assert len(render_args["pages_data"]) == 1  # Correct parameter name

    @patch("app.ai.text_processor.logger")
    def test_process_pages_logging(self, mock_logger, mock_genai_client, sample_metadata):
        """Test that appropriate logging occurs."""
        processor = TextProcessor(mock_genai_client, "test-model")

        pages = [
            PageData(
                title="Page 1",
                story_text="Text 1",
                illustration_prompt="Prompt 1",
            )
        ]

        mock_genai_client.models.generate_content.side_effect = Exception("API Error")

        processor.process_pages(pages=pages, metadata=sample_metadata)

        # Should log the error
        mock_logger.error.assert_called()