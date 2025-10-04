from ui.chat import render_chat
import streamlit as st
from core.settings import settings
from core.logger import logger
from langchain.globals import set_debug

set_debug(True)

st.set_page_config(page_title=settings.app.name, page_icon=settings.app.icon)
st.title(settings.app.title)

if __name__ == "__main__":
    logger.info("Starting chat application.")
    render_chat()
