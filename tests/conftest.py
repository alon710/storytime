"""Shared test fixtures and configuration."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.schemas import (
    ArtStyle,
    Gender,
    GeneratedPage,
    Language,
    PageData,
    StoryMetadata,
    StoryTemplate,
)


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for testing."""
    with patch("streamlit.session_state", {}):
        with patch("streamlit.write") as mock_write:
            with patch("streamlit.error") as mock_error:
                with patch("streamlit.success") as mock_success:
                    with patch("streamlit.info") as mock_info:
                        with patch("streamlit.warning") as mock_warning:
                            yield {
                                "write": mock_write,
                                "error": mock_error,
                                "success": mock_success,
                                "info": mock_info,
                                "warning": mock_warning,
                            }


@pytest.fixture
def mock_genai_client():
    """Mock Google GenAI client."""
    client = MagicMock()
    response = MagicMock()
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [MagicMock()]
    response.candidates[0].content.parts[0].text = "Generated content"
    client.models.generate_content.return_value = response
    return client


@pytest.fixture
def sample_metadata():
    """Sample story metadata for testing."""
    return StoryMetadata(
        character_name="Alice",
        age=7,
        gender=Gender.girl,
        language=Language.english,
        art_style=ArtStyle.watercolor,
        instructions="Make it magical and fun",
    )


@pytest.fixture
def sample_page_data():
    """Sample page data for testing."""
    return PageData(
        title="The Beginning",
        story_text="Once upon a time, there was a brave girl named Alice.",
        illustration_prompt="A young girl standing in a magical forest",
    )


@pytest.fixture
def sample_story_template():
    """Sample story template for testing."""
    return StoryTemplate(
        name="Adventure Story",
        description="An exciting adventure story",
        default_title="Alice's Adventure",
        pages=[
            PageData(
                title="The Beginning",
                story_text="Once upon a time, there was a brave girl named {character_name}.",
                illustration_prompt="A young {gender} standing in a magical forest",
            ),
            PageData(
                title="The Journey",
                story_text="{character_name} embarked on an amazing journey.",
                illustration_prompt="{character_name} walking on a winding path",
            ),
            PageData(
                title="The End",
                story_text="And {character_name} lived happily ever after.",
                illustration_prompt="{character_name} smiling happily at home",
            ),
        ],
    )


@pytest.fixture
def sample_generated_pages():
    """Sample generated pages for testing."""
    return [
        GeneratedPage(
            page_number=1,
            title="The Beginning",
            text="Once upon a time, there was a brave girl named Alice.",
            illustration_prompt="A young girl standing in a magical forest",
            image_path="/tmp/page_1.png",
        ),
        GeneratedPage(
            page_number=2,
            title="The Journey",
            text="Alice embarked on an amazing journey.",
            illustration_prompt="Alice walking on a winding path",
            image_path="/tmp/page_2.png",
        ),
        GeneratedPage(
            page_number=3,
            title="The End",
            text="And Alice lived happily ever after.",
            illustration_prompt="Alice smiling happily at home",
            image_path="/tmp/page_3.png",
        ),
    ]


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "GOOGLE_API_KEY": "test-api-key",
        "MODEL": "test-model",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_image_file(temp_dir: Path) -> Path:
    """Create a mock image file for testing."""
    from PIL import Image

    image_path = temp_dir / "test_image.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path)
    return image_path


@pytest.fixture
def mock_json_template(temp_dir: Path) -> Path:
    """Create a mock JSON template file for testing."""
    import json

    template_data = {
        "name": "Test Template",
        "description": "A test template",
        "default_title": "Test Story",
        "pages": [
            {
                "title": "Page 1",
                "story_text": "Text for page 1",
                "illustration_prompt": "Prompt for page 1",
            },
            {
                "title": "Page 2",
                "story_text": "Text for page 2",
                "illustration_prompt": "Prompt for page 2",
            },
        ],
    }

    template_path = temp_dir / "test_template.json"
    with open(template_path, "w") as f:
        json.dump(template_data, f)
    return template_path


@pytest.fixture(autouse=True)
def reset_streamlit_session():
    """Reset Streamlit session state before each test."""
    if hasattr(sys.modules.get("streamlit"), "session_state"):
        import streamlit as st

        st.session_state.clear()