from app.ui.pages.storytime import main
import streamlit as st


st.set_page_config(
    page_title="StoryTime",
    page_icon=None,
    layout="centered",
)

st.title("StoryTime")
st.caption("AI-Powered Story Generator")
st.divider()


if __name__ == "__main__":
    main()
