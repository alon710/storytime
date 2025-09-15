"""Unit tests for the download_manager module."""

import json
import zipfile
from pathlib import Path
from unittest.mock import patch


from app.utils.download_manager import DownloadManager
from app.utils.schemas import (
    Gender,
    GeneratedPage,
    StoryMetadata,
)


class TestDownloadManager:
    """Test DownloadManager class."""

    def test_create_story_text(self, sample_generated_pages):
        """Test creating story text from pages."""
        story_text = DownloadManager.create_story_text(sample_generated_pages)

        assert "Page 1: The Beginning" in story_text
        assert "Page 2: The Journey" in story_text
        assert "Page 3: The End" in story_text
        assert "Once upon a time, there was a brave girl named Alice" in story_text
        assert "Alice embarked on an amazing journey" in story_text
        assert "And Alice lived happily ever after" in story_text
        assert "-" * 40 in story_text

    def test_create_story_text_with_edited_text(self):
        """Test creating story text with edited text."""
        pages = [
            GeneratedPage(
                page_number=1,
                title="Title",
                text="Original text",
                edited_text="Edited text",
                illustration_prompt="Prompt",
            )
        ]
        story_text = DownloadManager.create_story_text(pages)

        assert "Edited text" in story_text
        assert "Original text" not in story_text

    def test_create_story_text_empty_pages(self):
        """Test creating story text with no pages."""
        story_text = DownloadManager.create_story_text([])
        assert story_text == ""

    def test_create_metadata_dict(
        self, sample_generated_pages, sample_metadata, sample_story_template
    ):
        """Test creating metadata dictionary."""
        metadata_dict = DownloadManager.create_metadata_dict(
            pages=sample_generated_pages,
            story_title="Test Story",
            metadata=sample_metadata,
            template=sample_story_template,
        )

        assert metadata_dict["story_title"] == "Test Story"
        assert metadata_dict["total_pages"] == 3
        assert metadata_dict["language"] == "English"
        assert metadata_dict["character"]["name"] == "Alice"
        assert metadata_dict["character"]["age"] == 7
        assert metadata_dict["character"]["gender"] == "Girl"
        assert metadata_dict["art_style"] == "watercolor"
        assert metadata_dict["instructions"] == "Make it magical and fun"
        assert metadata_dict["template_name"] == "Adventure Story"
        assert metadata_dict["template_description"] == "An exciting adventure story"
        assert len(metadata_dict["pages"]) == 3

    def test_create_metadata_dict_without_template(
        self, sample_generated_pages, sample_metadata
    ):
        """Test creating metadata dictionary without template."""
        metadata_dict = DownloadManager.create_metadata_dict(
            pages=sample_generated_pages,
            story_title="Test Story",
            metadata=sample_metadata,
            template=None,
        )

        assert "template_name" not in metadata_dict
        assert "template_description" not in metadata_dict
        assert metadata_dict["story_title"] == "Test Story"

    def test_create_metadata_dict_without_instructions(self, sample_generated_pages):
        """Test creating metadata dictionary without instructions."""
        metadata = StoryMetadata(
            character_name="Bob",
            age=5,
            gender=Gender.boy,
        )
        metadata_dict = DownloadManager.create_metadata_dict(
            pages=sample_generated_pages,
            story_title="Test Story",
            metadata=metadata,
        )

        assert "instructions" not in metadata_dict

    def test_create_metadata_dict_page_info(self, sample_generated_pages):
        """Test page information in metadata dictionary."""
        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
        )
        metadata_dict = DownloadManager.create_metadata_dict(
            pages=sample_generated_pages,
            story_title="Test Story",
            metadata=metadata,
        )

        page_info = metadata_dict["pages"][0]
        assert page_info["page_number"] == 1
        assert page_info["title"] == "The Beginning"
        assert page_info["illustration_prompt"] == "A young girl standing in a magical forest"
        assert page_info["has_image"] is False  # Path doesn't exist

    @patch("os.path.exists")
    def test_create_metadata_dict_with_existing_images(
        self, mock_exists, sample_generated_pages
    ):
        """Test metadata with existing image files."""
        mock_exists.return_value = True
        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
        )
        metadata_dict = DownloadManager.create_metadata_dict(
            pages=sample_generated_pages,
            story_title="Test Story",
            metadata=metadata,
        )

        for page_info in metadata_dict["pages"]:
            assert page_info["has_image"] is True

    def test_create_archive_success(self, sample_generated_pages, sample_metadata, temp_dir):
        """Test successfully creating an archive."""
        # Create actual image files
        for page in sample_generated_pages:
            if page.image_path:
                image_path = temp_dir / Path(page.image_path).name
                image_path.write_text("fake image data")
                page.image_path = str(image_path)

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = str(
                temp_dir / "test.zip"
            )

            zip_path = DownloadManager.create_archive(
                pages=sample_generated_pages,
                story_title="Test Story",
                metadata=sample_metadata,
            )

            assert zip_path is not None
            assert zip_path.endswith(".zip")

            # Verify zip contents
            with zipfile.ZipFile(zip_path, "r") as zipf:
                namelist = zipf.namelist()
                assert "story.txt" in namelist
                assert "metadata.json" in namelist
                assert "page_01.png" in namelist
                assert "page_02.png" in namelist
                assert "page_03.png" in namelist

                # Verify story text content
                story_content = zipf.read("story.txt").decode("utf-8")
                assert "Page 1: The Beginning" in story_content

                # Verify metadata content
                metadata_content = json.loads(zipf.read("metadata.json").decode("utf-8"))
                assert metadata_content["story_title"] == "Test Story"
                assert metadata_content["character"]["name"] == "Alice"

    def test_create_archive_missing_images(
        self, sample_generated_pages, sample_metadata, temp_dir
    ):
        """Test creating archive with missing image files."""
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = str(
                temp_dir / "test.zip"
            )

            zip_path = DownloadManager.create_archive(
                pages=sample_generated_pages,
                story_title="Test Story",
                metadata=sample_metadata,
            )

            assert zip_path is not None

            with zipfile.ZipFile(zip_path, "r") as zipf:
                namelist = zipf.namelist()
                assert "story.txt" in namelist
                assert "metadata.json" in namelist
                # Image files should not be included if they don't exist
                assert "page_01.png" not in namelist

    def test_create_archive_no_images(self, sample_metadata):
        """Test creating archive with pages that have no images."""
        pages = [
            GeneratedPage(
                page_number=1,
                title="Title",
                text="Text",
                illustration_prompt="Prompt",
                image_path=None,
            )
        ]

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            temp_path = "/tmp/test.zip"
            mock_temp.return_value.__enter__.return_value.name = temp_path

            zip_path = DownloadManager.create_archive(
                pages=pages,
                story_title="Test Story",
                metadata=sample_metadata,
            )

            assert zip_path == temp_path

    @patch("zipfile.ZipFile")
    @patch("tempfile.NamedTemporaryFile")
    def test_create_archive_exception_handling(
        self, mock_temp, mock_zip, sample_generated_pages, sample_metadata
    ):
        """Test archive creation with exception."""
        mock_temp.return_value.__enter__.return_value.name = "/tmp/test.zip"
        mock_zip.side_effect = Exception("Zip error")

        zip_path = DownloadManager.create_archive(
            pages=sample_generated_pages,
            story_title="Test Story",
            metadata=sample_metadata,
        )

        assert zip_path is None

    def test_create_archive_unicode_content(self, sample_metadata, temp_dir):
        """Test creating archive with Unicode content."""
        pages = [
            GeneratedPage(
                page_number=1,
                title="Title with émojis 🎉",
                text="Text with special characters: é, ñ, 中文",
                illustration_prompt="Prompt",
            )
        ]

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = str(
                temp_dir / "test.zip"
            )

            zip_path = DownloadManager.create_archive(
                pages=pages,
                story_title="Story with émojis 📚",
                metadata=sample_metadata,
            )

            assert zip_path is not None

            with zipfile.ZipFile(zip_path, "r") as zipf:
                story_content = zipf.read("story.txt").decode("utf-8")
                assert "émojis 🎉" in story_content
                assert "中文" in story_content

                metadata_content = json.loads(zipf.read("metadata.json").decode("utf-8"))
                assert metadata_content["story_title"] == "Story with émojis 📚"