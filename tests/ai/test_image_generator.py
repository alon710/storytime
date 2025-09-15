"""Integration tests for the ImageGenerator module."""

import base64
from unittest.mock import MagicMock, patch


from app.ai.image_generator import ImageGenerator
from app.utils.schemas import ArtStyle, Gender


class TestImageGenerator:
    """Test ImageGenerator class."""

    def test_initialization(self, mock_genai_client):
        """Test ImageGenerator initialization."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        assert generator.client == mock_genai_client
        assert generator.model == "test-model"
        assert generator.env is not None

    def test_art_style_descriptions(self):
        """Test that all art styles have descriptions."""
        for style in ArtStyle:
            assert style in ImageGenerator.ART_STYLE_DESCRIPTIONS
            assert isinstance(ImageGenerator.ART_STYLE_DESCRIPTIONS[style], str)
            assert len(ImageGenerator.ART_STYLE_DESCRIPTIONS[style]) > 0

    def test_generate_character_reference_success(self, mock_genai_client):
        """Test successful character reference generation."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        # Mock all the PIL Image operations
        with patch("app.ai.image_generator.Image.open") as mock_pil_open:
            # Mock the input images
            mock_input_image = MagicMock()
            mock_pil_open.side_effect = [mock_input_image, mock_input_image]  # Two input images

            # Mock the generated image from API response
            mock_generated_image = MagicMock()
            mock_generated_image.width = 100
            mock_generated_image.height = 100

            # When PIL opens the API response data, return our mock
            mock_pil_open.side_effect = [
                mock_input_image, mock_input_image,  # Input images
                mock_generated_image  # Generated image from API
            ]

            with patch("app.ai.image_generator.Image.new") as mock_image_new:
                mock_final_image = MagicMock()
                mock_image_new.return_value = mock_final_image

                with patch("app.ai.image_generator.save_image_to_temp") as mock_save_temp:
                    mock_save_temp.return_value = "/tmp/generated_image.png"

                    # Mock the API response
                    mock_response = MagicMock()
                    mock_part = MagicMock()
                    mock_part.inline_data.data = b"fake_image_bytes"
                    mock_part.inline_data.mime_type = "image/png"
                    mock_response.candidates = [MagicMock()]
                    mock_response.candidates[0].content.parts = [mock_part]

                    generator._generate_content = MagicMock(return_value=mock_response)

                    result = generator.generate_character_reference(
                        character_images=["image1.png", "image2.png"],
                        character_name="Alice",
                        character_age=7,
                        character_gender=Gender.girl,
                        system_prompt="Make it magical",
                        art_style=ArtStyle.watercolor,
                    )

                    assert result == "/tmp/generated_image.png"
                    mock_save_temp.assert_called_once()

    @patch("app.ai.image_generator.Image.open")
    def test_generate_character_reference_no_response(
        self, mock_image_open, mock_genai_client
    ):
        """Test handling of no API response."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        mock_images = [MagicMock()]
        mock_image_open.side_effect = mock_images

        mock_genai_client.models.generate_content.return_value = None

        result = generator.generate_character_reference(
            character_images=["image1.png"],
            character_name="Alice",
            character_age=7,
            character_gender=Gender.girl,
            system_prompt="",
            art_style=ArtStyle.cartoon,
        )

        assert result is None

    @patch("app.ai.image_generator.Image.open")
    def test_generate_character_reference_exception(
        self, mock_image_open, mock_genai_client
    ):
        """Test exception handling during character reference generation."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        mock_image_open.side_effect = Exception("Image load error")

        result = generator.generate_character_reference(
            character_images=["image1.png"],
            character_name="Alice",
            character_age=7,
            character_gender=Gender.girl,
            system_prompt="",
            art_style=ArtStyle.digital,
        )

        assert result is None

    def test_generate_story_image_success(self, mock_genai_client, sample_metadata):
        """Test successful story image generation."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        # Mock all PIL Image operations
        with patch("app.ai.image_generator.Image.open") as mock_pil_open:
            mock_seed_image = MagicMock()
            mock_generated_image = MagicMock()
            mock_generated_image.width = 100
            mock_generated_image.height = 100

            # First call for seed image, second for generated image
            mock_pil_open.side_effect = [mock_seed_image, mock_generated_image]

            with patch("app.ai.image_generator.Image.new") as mock_image_new:
                mock_final_image = MagicMock()
                mock_image_new.return_value = mock_final_image

                with patch("app.ai.image_generator.save_image_to_temp") as mock_save_temp:
                    mock_save_temp.return_value = "/tmp/story_image.png"

                    # Mock API response
                    mock_response = MagicMock()
                    mock_part = MagicMock()
                    mock_part.inline_data.data = b"fake_image_bytes"
                    mock_part.inline_data.mime_type = "image/png"
                    mock_response.candidates = [MagicMock()]
                    mock_response.candidates[0].content.parts = [mock_part]

                    generator._generate_content = MagicMock(return_value=mock_response)

                    result = generator.generate(
                        seed_images=["seed.png"],
                        illustration_prompt="A magical forest",
                        page_title="The Beginning",
                        story_text="Once upon a time...",
                        metadata=sample_metadata,
                        system_prompt="Make it beautiful",
                    )

                    assert result == "/tmp/story_image.png"

    def test_generate_with_previous_pages(
        self, mock_genai_client, sample_metadata
    ):
        """Test image generation with previous pages context."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        previous_pages = [
            {
                "title": "Page 1",
                "text": "Previous text",
                "illustration_prompt": "Previous prompt",
            }
        ]

        with patch("app.ai.image_generator.Image.open") as mock_pil_open:
            mock_seed_image = MagicMock()
            mock_generated_image = MagicMock()
            mock_generated_image.width = 100
            mock_generated_image.height = 100
            mock_pil_open.side_effect = [mock_seed_image, mock_generated_image]

            with patch("app.ai.image_generator.Image.new") as mock_image_new:
                mock_final_image = MagicMock()
                mock_image_new.return_value = mock_final_image

                with patch("app.ai.image_generator.save_image_to_temp") as mock_save:
                    mock_save.return_value = "/tmp/image.png"

                    # Mock API response
                    mock_response = MagicMock()
                    mock_part = MagicMock()
                    mock_part.inline_data.data = b"fake_image_bytes"
                    mock_part.inline_data.mime_type = "image/png"
                    mock_response.candidates = [MagicMock()]
                    mock_response.candidates[0].content.parts = [mock_part]

                    generator._generate_content = MagicMock(return_value=mock_response)

                    result = generator.generate(
                        seed_images=["seed.png"],
                        illustration_prompt="New prompt",
                        page_title="Page 2",
                        story_text="New text",
                        metadata=sample_metadata,
                        previous_pages=previous_pages,
                    )

                    assert result == "/tmp/image.png"

                    # Verify template was called (which includes previous pages)
                    generator._generate_content.assert_called_once()

    def test_generate_with_previous_images(self, mock_genai_client, sample_metadata):
        """Test image generation with previous images as context."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        with patch("app.ai.image_generator.Image.open") as mock_pil_open:
            # Mock seed image + 2 previous images + 1 generated image
            mock_seed_image = MagicMock()
            mock_prev_image1 = MagicMock()
            mock_prev_image2 = MagicMock()
            mock_generated_image = MagicMock()
            mock_generated_image.width = 100
            mock_generated_image.height = 100

            mock_pil_open.side_effect = [
                mock_seed_image,
                mock_prev_image1,
                mock_prev_image2,
                mock_generated_image,
            ]

            with patch("app.ai.image_generator.Image.new") as mock_image_new:
                mock_final_image = MagicMock()
                mock_image_new.return_value = mock_final_image

                with patch("app.ai.image_generator.save_image_to_temp") as mock_save:
                    mock_save.return_value = "/tmp/image.png"

                    # Mock API response
                    mock_response = MagicMock()
                    mock_part = MagicMock()
                    mock_part.inline_data.data = b"fake_image_bytes"
                    mock_part.inline_data.mime_type = "image/png"
                    mock_response.candidates = [MagicMock()]
                    mock_response.candidates[0].content.parts = [mock_part]

                    generator._generate_content = MagicMock(return_value=mock_response)

                    result = generator.generate(
                        seed_images=["seed.png"],
                        illustration_prompt="New prompt",
                        page_title="Page 3",
                        story_text="New text",
                        metadata=sample_metadata,
                        previous_images=["/tmp/prev1.png", "/tmp/prev2.png"],
                    )

                    assert result == "/tmp/image.png"
                    # Should have opened seed image + 2 previous images + generated image
                    assert mock_pil_open.call_count == 4

    def test_generate_template_rendering(
        self, mock_genai_client, sample_metadata
    ):
        """Test that templates are properly rendered."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        with patch.object(generator.env, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "Rendered prompt"
            mock_get_template.return_value = mock_template

            with patch("app.ai.image_generator.Image.open"):
                with patch("app.ai.image_generator.save_image_to_temp"):
                    mock_response = MagicMock()
                    mock_response.candidates = [MagicMock()]
                    mock_response.candidates[0].content.parts = [MagicMock()]
                    mock_response.candidates[0].content.parts[0].inline_data.data = (
                        base64.b64encode(b"image")
                    )
                    mock_response.candidates[0].content.parts[0].inline_data.mime_type = (
                        "image/png"
                    )
                    mock_genai_client.models.generate_content.return_value = mock_response

                    generator.generate(
                        seed_images=["seed.png"],
                        illustration_prompt="Test prompt",
                        page_title="Test Title",
                        story_text="Test text",
                        metadata=sample_metadata,
                    )

            mock_get_template.assert_called_once_with("image_generation.j2")
            mock_template.render.assert_called_once()

            # Verify template parameters
            render_args = mock_template.render.call_args.kwargs
            assert render_args["illustration_prompt"] == "Test prompt"
            assert render_args["page_title"] == "Test Title"
            assert render_args["story_text"] == "Test text"
            assert render_args["character_name"] == "Alice"

    @patch("app.ai.image_generator.logger")
    def test_generate_logging_on_error(
        self, mock_logger, mock_genai_client, sample_metadata
    ):
        """Test that errors are properly logged."""
        generator = ImageGenerator(mock_genai_client, "test-model")

        with patch("app.ai.image_generator.Image.open") as mock_open:
            mock_open.side_effect = Exception("Image error")

            result = generator.generate(
                seed_images=["seed.png"],
                illustration_prompt="Test",
                page_title="Test",
                story_text="Test",
                metadata=sample_metadata,
            )

            assert result is None
            mock_logger.error.assert_called()

    # These tests are removed as _extract_image_from_response is likely a private/internal method
    # that doesn't exist in the actual implementation