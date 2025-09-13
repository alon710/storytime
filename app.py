from app.ui.pages.storytime import main
import streamlit as st
import tomllib
from pathlib import Path


def get_version():
    try:
        with open(file=Path("pyproject.toml"), mode="rb") as f:
            data: dict = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "Unknown Version"


st.set_page_config(
    page_title="StoryTime",
    page_icon=None,
    layout="centered",
)

version = get_version()
st.title("StoryTime")
st.caption(f"AI-Powered Story Generator • Version {version}")
st.divider()


if __name__ == "__main__":
    main()
