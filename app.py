import streamlit as st
import tomllib


def get_version():
    try:
        with open(file="pyproject.toml", mode="rb") as f:
            data: dict = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "Unknown Version"


st.set_page_config(
    page_title="StoryTime",
    page_icon="🐤",
    layout="centered",
)

version = get_version()


story_generator = st.Page(
    "pages/1_story_generator.py",
    title="Story Generator",
    icon="📚",
)

character_creator = st.Page(
    "pages/2_character_creator.py",
    title="Character Creator",
    icon="🎨",
)

pg = st.navigation(
    [story_generator, character_creator],
    position="top",
)

st.markdown("# 🐤 StoryTime")
st.caption(f"Version {version}")
st.divider()

pg.run()
