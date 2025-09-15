"""Unit tests for the utils module."""

import json
from unittest.mock import MagicMock, mock_open, patch


from app.utils.schemas import SessionStateKeys
from app.utils.utils import initialize_session_state, load_story_templates


class TestLoadStoryTemplates:
    """Test load_story_templates function."""

    @patch("app.utils.utils.Path.exists")
    @patch("app.utils.utils.Path.glob")
    def test_load_story_templates_success(self, mock_glob, mock_exists):
        """Test successfully loading story templates."""
        mock_exists.return_value = True

        # Create mock template files
        template1_data = {
            "name": "Template 1",
            "description": "Description 1",
            "default_title": "Title 1",
            "pages": [
                {
                    "title": "Page 1",
                    "story_text": "Text 1",
                    "illustration_prompt": "Prompt 1",
                }
            ],
        }
        template2_data = {
            "name": "Template 2",
            "description": "Description 2",
            "default_title": "Title 2",
            "pages": [
                {
                    "title": "Page 2",
                    "story_text": "Text 2",
                    "illustration_prompt": "Prompt 2",
                }
            ],
        }

        mock_file1 = MagicMock()
        mock_file1.stem = "template1"
        mock_file1.name = "template1.json"

        mock_file2 = MagicMock()
        mock_file2.stem = "template2"
        mock_file2.name = "template2.json"

        mock_glob.return_value = [mock_file1, mock_file2]

        with patch("builtins.open", mock_open()) as mock_file:
            # Configure the mock to return different data for each file
            mock_file.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(template1_data),
                json.dumps(template2_data),
            ]

            # Mock json.load to return the appropriate data
            with patch("json.load") as mock_json_load:
                mock_json_load.side_effect = [template1_data, template2_data]

                templates = load_story_templates()

        assert len(templates) == 2
        assert "template1" in templates
        assert "template2" in templates
        assert templates["template1"].name == "Template 1"
        assert templates["template2"].name == "Template 2"

    @patch("app.utils.utils.Path.exists")
    def test_load_story_templates_no_directory(self, mock_exists):
        """Test loading templates when directory doesn't exist."""
        mock_exists.return_value = False
        templates = load_story_templates()
        assert templates == {}

    @patch("app.utils.utils.Path.exists")
    @patch("app.utils.utils.Path.glob")
    def test_load_story_templates_empty_directory(self, mock_glob, mock_exists):
        """Test loading templates from empty directory."""
        mock_exists.return_value = True
        mock_glob.return_value = []
        templates = load_story_templates()
        assert templates == {}

    @patch("app.utils.utils.Path.exists")
    @patch("app.utils.utils.Path.glob")
    @patch("streamlit.error")
    def test_load_story_templates_invalid_json(
        self, mock_error, mock_glob, mock_exists
    ):
        """Test handling invalid JSON in template file."""
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.stem = "invalid"
        mock_file.name = "invalid.json"
        mock_glob.return_value = [mock_file]

        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
                templates = load_story_templates()

        assert templates == {}
        mock_error.assert_called_once()

    @patch("app.utils.utils.Path.exists")
    @patch("app.utils.utils.Path.glob")
    def test_load_story_templates_missing_fields(self, mock_glob, mock_exists):
        """Test loading template with missing required fields."""
        mock_exists.return_value = True

        template_data = {
            "description": "Description",
            # Missing 'name' and other required fields
        }

        mock_file = MagicMock()
        mock_file.stem = "incomplete"
        mock_file.name = "incomplete.json"
        mock_glob.return_value = [mock_file]

        with patch("builtins.open", mock_open()):
            with patch("json.load", return_value=template_data):
                templates = load_story_templates()

        # Should use stem as name and handle missing fields gracefully
        assert "incomplete" in templates
        assert templates["incomplete"].name == "incomplete"


class TestInitializeSessionState:
    """Test initialize_session_state function."""

    @patch("streamlit.session_state", {})
    def test_initialize_session_state_empty(self):
        """Test initializing empty session state."""
        initialize_session_state()

        import streamlit as st

        assert SessionStateKeys.SEED_IMAGES in st.session_state
        assert SessionStateKeys.METADATA in st.session_state
        assert SessionStateKeys.STORY_TEMPLATE in st.session_state
        assert SessionStateKeys.EDITED_TEMPLATE in st.session_state
        assert SessionStateKeys.GENERATED_PAGES in st.session_state
        assert SessionStateKeys.SYSTEM_PROMPT in st.session_state

        assert st.session_state[SessionStateKeys.SEED_IMAGES] == []
        assert st.session_state[SessionStateKeys.METADATA] is None
        assert st.session_state[SessionStateKeys.STORY_TEMPLATE] is None
        assert st.session_state[SessionStateKeys.EDITED_TEMPLATE] is None
        assert st.session_state[SessionStateKeys.GENERATED_PAGES] == []
        assert st.session_state[SessionStateKeys.SYSTEM_PROMPT] == ""

    @patch("streamlit.session_state", {SessionStateKeys.SEED_IMAGES: ["existing"]})
    def test_initialize_session_state_preserve_existing(self):
        """Test that existing session state values are preserved."""
        initialize_session_state()

        import streamlit as st

        # Existing value should be preserved
        assert st.session_state[SessionStateKeys.SEED_IMAGES] == ["existing"]

        # New keys should be added
        assert SessionStateKeys.METADATA in st.session_state
        assert st.session_state[SessionStateKeys.METADATA] is None

    @patch("streamlit.session_state", {})
    def test_initialize_session_state_all_keys(self):
        """Test that all expected keys are initialized."""
        initialize_session_state()

        import streamlit as st

        expected_keys = [
            SessionStateKeys.SEED_IMAGES,
            SessionStateKeys.METADATA,
            SessionStateKeys.STORY_TEMPLATE,
            SessionStateKeys.EDITED_TEMPLATE,
            SessionStateKeys.GENERATED_PAGES,
            SessionStateKeys.SYSTEM_PROMPT,
        ]

        for key in expected_keys:
            assert key in st.session_state