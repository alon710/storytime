from ui.chat import run_chat
import streamlit as st
from core.settings import settings

st.set_page_config(page_title=settings.app.name, page_icon=settings.app.icon)
st.title(settings.app.title)

if __name__ == "__main__":
    run_chat()
