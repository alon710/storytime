"""Integration tests for the StoryProcessor module."""

from unittest.mock import MagicMock, patch


from app.ai.story_processor import StoryProcessor
from app.utils.schemas import GeneratedPage, StoryTemplate


class TestStoryProcessor:
    """Test StoryProcessor class."""

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_initialization(self, mock_genai_client_class, mock_settings):
        """Test StoryProcessor initialization."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"
        mock_client = MagicMock()
        mock_genai_client_class.return_value = mock_client

        processor = StoryProcessor()

        assert processor.image_generator is not None
        assert processor.text_processor is not None
        mock_genai_client_class.assert_called_once_with(api_key="test-key")

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_success(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test successful story generation."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        # Mock text processor
        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {
                0: "Processed text for page 1",
                1: "Processed text for page 2",
                2: "Processed text for page 3",
            }

            # Mock image generator
            with patch.object(processor.image_generator, "generate") as mock_image:
                mock_image.side_effect = [
                    "/tmp/image1.png",
                    "/tmp/image2.png",
                    "/tmp/image3.png",
                ]

                result = processor.generate_story(
                    story_template=sample_story_template,
                    metadata=sample_metadata,
                    seed_images=["seed.png"],
                )

        assert len(result) == 3
        assert all(isinstance(page, GeneratedPage) for page in result)
        assert result[0].page_number == 1
        assert result[0].text == "Processed text for page 1"
        assert result[0].image_path == "/tmp/image1.png"

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_without_seed_images(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test story generation without seed images."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {
                0: "Processed text 1",
                1: "Processed text 2",
                2: "Processed text 3",
            }

            result = processor.generate_story(
                story_template=sample_story_template,
                metadata=sample_metadata,
                seed_images=None,
            )

        assert len(result) == 3
        assert all(page.image_path is None for page in result)
        assert all(page.text.startswith("Processed text") for page in result)

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_with_text_processing_failure(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test story generation when text processing fails."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {}  # Empty result indicates failure

            with patch.object(processor.image_generator, "generate") as mock_image:
                mock_image.return_value = "/tmp/image.png"

                result = processor.generate_story(
                    story_template=sample_story_template,
                    metadata=sample_metadata,
                    seed_images=["seed.png"],
                )

        # Should still generate with original text
        assert len(result) == 3
        assert result[0].text == sample_story_template.pages[0].story_text

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_with_image_generation_failure(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test story generation when image generation fails."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {0: "Text 1", 1: "Text 2", 2: "Text 3"}

            with patch.object(processor.image_generator, "generate") as mock_image:
                mock_image.return_value = None  # Simulate failure

                result = processor.generate_story(
                    story_template=sample_story_template,
                    metadata=sample_metadata,
                    seed_images=["seed.png"],
                )

        assert len(result) == 3
        assert all(page.image_path is None for page in result)
        assert all(page.text for page in result)  # Text should still be present

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_with_previous_context(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test that previous pages context is passed correctly."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {0: "Text 1", 1: "Text 2", 2: "Text 3"}

            with patch.object(processor.image_generator, "generate") as mock_image:
                mock_image.side_effect = ["/tmp/img1.png", "/tmp/img2.png", "/tmp/img3.png"]

                processor.generate_story(
                    story_template=sample_story_template,
                    metadata=sample_metadata,
                    seed_images=["seed.png"],
                )

                # Check that previous pages were passed correctly for the third page
                third_call = mock_image.call_args_list[2]
                previous_pages = third_call.kwargs["previous_pages"]
                previous_images = third_call.kwargs["previous_images"]

                assert len(previous_pages) == 2
                assert previous_pages[0]["title"] == "The Beginning"
                assert len(previous_images) == 2
                assert previous_images[0] == "/tmp/img1.png"

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    @patch("app.ai.story_processor.logger")
    def test_generate_story_exception_handling(
        self, mock_logger, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test exception handling during story generation."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.side_effect = Exception("Processing error")

            result = processor.generate_story(
                story_template=sample_story_template,
                metadata=sample_metadata,
            )

        assert result == []
        mock_logger.error.assert_called()

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_empty_template(
        self, mock_genai_client_class, mock_settings, sample_metadata
    ):
        """Test story generation with empty template."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        empty_template = StoryTemplate(
            name="Empty",
            description="Empty template",
            default_title="Empty",
            pages=[],
        )

        result = processor.generate_story(
            story_template=empty_template,
            metadata=sample_metadata,
        )

        assert result == []

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_page_numbering(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test that pages are numbered correctly."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {0: "Text 1", 1: "Text 2", 2: "Text 3"}

            result = processor.generate_story(
                story_template=sample_story_template,
                metadata=sample_metadata,
            )

        assert result[0].page_number == 1
        assert result[1].page_number == 2
        assert result[2].page_number == 3

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    def test_generate_story_preserves_template_data(
        self, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test that template data is preserved in generated pages."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {}  # No processing

            result = processor.generate_story(
                story_template=sample_story_template,
                metadata=sample_metadata,
            )

        for i, page in enumerate(result):
            assert page.title == sample_story_template.pages[i].title
            assert page.illustration_prompt == sample_story_template.pages[i].illustration_prompt

    @patch("app.ai.story_processor.settings")
    @patch("app.ai.story_processor.genai.Client")
    @patch("app.ai.story_processor.logger")
    def test_generate_story_logging(
        self, mock_logger, mock_genai_client_class, mock_settings, sample_story_template, sample_metadata
    ):
        """Test that appropriate logging occurs during story generation."""
        mock_settings.google_api_key = "test-key"
        mock_settings.story_image_model = "test-image-model"
        mock_settings.story_text_model = "test-text-model"

        processor = StoryProcessor()

        with patch.object(processor.text_processor, "process_pages") as mock_text:
            mock_text.return_value = {0: "Text 1", 1: "Text 2", 2: "Text 3"}

            processor.generate_story(
                story_template=sample_story_template,
                metadata=sample_metadata,
            )

        # Should log info for each page and success message
        assert mock_logger.info.call_count >= 4  # 3 pages + 1 success message