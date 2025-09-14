from pathlib import Path
import streamlit as st

from streamlit import json
from app.utils.schemas import SessionStateKeys, StoryTemplate


def load_story_templates() -> dict[str, StoryTemplate]:
    templates = {}
    template_dir = Path("app/story_templates")

    if template_dir.exists():
        for template_file in template_dir.glob("*.json"):
            try:
                with open(template_file, "r") as f:
                    data = json.load(f)
                    templates[template_file.stem] = StoryTemplate(
                        name=data.get("name", template_file.stem),
                        description=data.get("description", ""),
                        default_title=data.get("default_title", "Story"),
                        pages=data.get("pages", []),
                    )
            except Exception as e:
                st.error(f"Error loading {template_file.name}: {str(e)}")

    return templates


def initialize_session_state() -> None:
    defaults = {
        SessionStateKeys.SEED_IMAGES: [],
        SessionStateKeys.METADATA: None,
        SessionStateKeys.STORY_TEMPLATE: None,
        SessionStateKeys.EDITED_TEMPLATE: None,
        SessionStateKeys.GENERATED_PAGES: [],
        SessionStateKeys.SYSTEM_PROMPT: "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
