"""Unit tests for the schemas module."""

import pytest
from pydantic import ValidationError

from app.utils.schemas import (
    ArtStyle,
    Gender,
    GeneratedPage,
    Language,
    PageData,
    ReferenceMethod,
    SeedImageData,
    SessionStateKeys,
    StoryMetadata,
    StoryTemplate,
    Suffix,
)


class TestEnums:
    """Test enum classes."""

    def test_gender_enum_values(self):
        """Test Gender enum values."""
        assert Gender.boy.value == "Boy"
        assert Gender.girl.value == "Girl"
        assert len(Gender) == 2

    def test_language_enum_values(self):
        """Test Language enum values."""
        assert Language.english.value == "English"
        assert Language.hebrew.value == "Hebrew"
        assert len(Language) == 2

    def test_reference_method_enum_values(self):
        """Test ReferenceMethod enum values."""
        assert ReferenceMethod.upload.value == "Upload Reference Image"
        assert ReferenceMethod.generate.value == "Generate from Photos"
        assert len(ReferenceMethod) == 2

    def test_art_style_enum_values(self):
        """Test ArtStyle enum values."""
        assert ArtStyle.watercolor.value == "watercolor"
        assert ArtStyle.cartoon.value == "cartoon"
        assert ArtStyle.ghibli.value == "ghibli"
        assert ArtStyle.vintage.value == "vintage"
        assert ArtStyle.digital.value == "digital"
        assert ArtStyle.pixar.value == "pixar"
        assert len(ArtStyle) == 6

    def test_suffix_enum_values(self):
        """Test Suffix enum values."""
        assert Suffix.png.value == ".png"
        assert Suffix.jpg.value == ".jpg"
        assert Suffix.jpeg.value == ".jpeg"
        assert len(Suffix) == 3


class TestSessionStateKeys:
    """Test SessionStateKeys class."""

    def test_session_state_keys(self):
        """Test all session state keys are defined."""
        expected_keys = [
            "SEED_IMAGES",
            "METADATA",
            "STORY_TEMPLATE",
            "EDITED_TEMPLATE",
            "GENERATED_PAGES",
            "SYSTEM_PROMPT",
            "CHAR_NAME",
            "CHAR_AGE",
            "CHAR_GENDER",
            "LANGUAGE",
            "GENERATED_CHARACTER_REF",
            "UPLOADED_REFERENCE",
            "ART_STYLE",
        ]
        for key in expected_keys:
            assert hasattr(SessionStateKeys, key)
            assert isinstance(getattr(SessionStateKeys, key), str)


class TestPageData:
    """Test PageData model."""

    def test_page_data_creation(self):
        """Test creating a valid PageData instance."""
        page = PageData(
            title="Test Title",
            story_text="Test story text",
            illustration_prompt="Test prompt",
        )
        assert page.title == "Test Title"
        assert page.story_text == "Test story text"
        assert page.illustration_prompt == "Test prompt"

    def test_page_data_validation(self):
        """Test PageData validation."""
        with pytest.raises(ValidationError):
            PageData(title="Test", story_text="Test")  # Missing illustration_prompt

    def test_page_data_json_serialization(self):
        """Test PageData JSON serialization."""
        page = PageData(
            title="Test Title",
            story_text="Test story text",
            illustration_prompt="Test prompt",
        )
        json_data = page.model_dump()
        assert json_data["title"] == "Test Title"
        assert json_data["story_text"] == "Test story text"
        assert json_data["illustration_prompt"] == "Test prompt"


class TestStoryMetadata:
    """Test StoryMetadata model."""

    def test_story_metadata_creation(self):
        """Test creating a valid StoryMetadata instance."""
        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
            language=Language.english,
            art_style=ArtStyle.watercolor,
            instructions="Test instructions",
        )
        assert metadata.character_name == "Alice"
        assert metadata.age == 7
        assert metadata.gender == Gender.girl
        assert metadata.language == Language.english
        assert metadata.art_style == ArtStyle.watercolor
        assert metadata.instructions == "Test instructions"

    def test_story_metadata_defaults(self):
        """Test StoryMetadata default values."""
        metadata = StoryMetadata(
            character_name="Bob",
            age=5,
            gender=Gender.boy,
        )
        assert metadata.language == Language.english
        assert metadata.art_style == ArtStyle.watercolor
        assert metadata.instructions is None

    def test_story_metadata_validation(self):
        """Test StoryMetadata validation."""
        # Test missing required field - create invalid data
        with pytest.raises(ValidationError):
            StoryMetadata()  # Missing all required fields

        # Test that valid data works
        valid_metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
        )
        assert valid_metadata.character_name == "Alice"
        assert valid_metadata.age == 7

    def test_story_metadata_json_serialization(self):
        """Test StoryMetadata JSON serialization."""
        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
        )
        json_data = metadata.model_dump()
        assert json_data["character_name"] == "Alice"
        assert json_data["age"] == 7
        assert json_data["gender"] == Gender.girl
        assert json_data["language"] == Language.english
        assert json_data["art_style"] == ArtStyle.watercolor


class TestSeedImageData:
    """Test SeedImageData model."""

    def test_seed_image_data_creation(self):
        """Test creating a valid SeedImageData instance."""
        metadata = StoryMetadata(
            character_name="Alice",
            age=7,
            gender=Gender.girl,
        )
        seed_data = SeedImageData(
            images=["/path/to/image1.png", "/path/to/image2.png"],
            metadata=metadata,
        )
        assert len(seed_data.images) == 2
        assert seed_data.metadata == metadata

    def test_seed_image_data_defaults(self):
        """Test SeedImageData default values."""
        seed_data = SeedImageData()
        assert seed_data.images == []
        assert seed_data.metadata is None

    def test_seed_image_data_json_serialization(self):
        """Test SeedImageData JSON serialization."""
        seed_data = SeedImageData(images=["/path/to/image.png"])
        json_data = seed_data.model_dump()
        assert json_data["images"] == ["/path/to/image.png"]
        assert json_data["metadata"] is None


class TestStoryTemplate:
    """Test StoryTemplate model."""

    def test_story_template_creation(self):
        """Test creating a valid StoryTemplate instance."""
        pages = [
            PageData(
                title="Page 1",
                story_text="Story 1",
                illustration_prompt="Prompt 1",
            ),
            PageData(
                title="Page 2",
                story_text="Story 2",
                illustration_prompt="Prompt 2",
            ),
        ]
        template = StoryTemplate(
            name="Test Template",
            description="Test description",
            default_title="Test Title",
            pages=pages,
        )
        assert template.name == "Test Template"
        assert template.description == "Test description"
        assert template.default_title == "Test Title"
        assert len(template.pages) == 2
        assert template.pages[0].title == "Page 1"

    def test_story_template_validation(self):
        """Test StoryTemplate validation."""
        with pytest.raises(ValidationError):
            StoryTemplate(
                name="Test",
                description="Test",
                default_title="Test",
                # Missing pages
            )

    def test_story_template_empty_pages(self):
        """Test StoryTemplate with empty pages list."""
        template = StoryTemplate(
            name="Test Template",
            description="Test description",
            default_title="Test Title",
            pages=[],
        )
        assert len(template.pages) == 0

    def test_story_template_json_serialization(self):
        """Test StoryTemplate JSON serialization."""
        pages = [
            PageData(
                title="Page 1",
                story_text="Story 1",
                illustration_prompt="Prompt 1",
            )
        ]
        template = StoryTemplate(
            name="Test Template",
            description="Test description",
            default_title="Test Title",
            pages=pages,
        )
        json_data = template.model_dump()
        assert json_data["name"] == "Test Template"
        assert len(json_data["pages"]) == 1


class TestGeneratedPage:
    """Test GeneratedPage model."""

    def test_generated_page_creation(self):
        """Test creating a valid GeneratedPage instance."""
        page = GeneratedPage(
            page_number=1,
            title="Test Title",
            text="Test text",
            edited_text="Edited text",
            image_path="/path/to/image.png",
            illustration_prompt="Test prompt",
        )
        assert page.page_number == 1
        assert page.title == "Test Title"
        assert page.text == "Test text"
        assert page.edited_text == "Edited text"
        assert page.image_path == "/path/to/image.png"
        assert page.illustration_prompt == "Test prompt"

    def test_generated_page_defaults(self):
        """Test GeneratedPage default values."""
        page = GeneratedPage(
            page_number=1,
            title="Test Title",
            text="Test text",
            illustration_prompt="Test prompt",
        )
        assert page.edited_text is None
        assert page.image_path is None

    def test_generated_page_validation(self):
        """Test GeneratedPage validation."""
        with pytest.raises(ValidationError):
            GeneratedPage(
                title="Test",
                text="Test",
                illustration_prompt="Test",
                # Missing page_number
            )

    def test_generated_page_json_serialization(self):
        """Test GeneratedPage JSON serialization."""
        page = GeneratedPage(
            page_number=1,
            title="Test Title",
            text="Test text",
            illustration_prompt="Test prompt",
        )
        json_data = page.model_dump()
        assert json_data["page_number"] == 1
        assert json_data["title"] == "Test Title"
        assert json_data["text"] == "Test text"
        assert json_data["edited_text"] is None
        assert json_data["image_path"] is None