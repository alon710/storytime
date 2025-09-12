import streamlit as st
import tomllib
import sys
from pathlib import Path

# Add pages directory to Python path
sys.path.append(str(Path(__file__).parent / "pages"))

# Import page modules using importlib to handle numbered filenames
import importlib.util


def import_page_module(filename):
    """Import a page module by filename"""
    module_path = Path(__file__).parent / "pages" / filename
    spec = importlib.util.spec_from_file_location(
        filename.replace(".py", ""), module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
