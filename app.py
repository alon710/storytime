"""
StoryTime - AI-Powered Children's Storybook Generator
Streamlit app with multipage navigation
"""

import streamlit as st
import tomllib


def get_version():
    """Get version from pyproject.toml"""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "Unknown Version"


def main():
    """Main Streamlit application with multipage navigation"""
    st.set_page_config(page_title="StoryTime", page_icon="📚", layout="wide")

    version = get_version()

    character_creator = st.Page(
        "pages/2_character_creator.py", title="Character Creator", icon="🎨"
    )

    story_generator = st.Page(
        "pages/1_story_generator.py",
        title="Story Generator",
        icon="📚",
        default=True,
    )

    pg = st.navigation([story_generator, character_creator])

    # Add header with version
    st.markdown("# StoryTime")
    st.markdown("Create AI-Illustrated Children's Storybooks")
    st.caption(f"Version {version}")
    st.divider()

    # Run the selected page
    pg.run()


if __name__ == "__main__":
    main()
