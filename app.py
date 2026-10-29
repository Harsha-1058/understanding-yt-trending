"""How a Video Gets Trending - Streamlit wrapper.

Serves the original designed HTML page (page.html) full-screen inside Streamlit,
so the UI, animations and charts are identical to the HTML version.
(The plain native-Streamlit version is kept in app_native.py.)
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="How a Video Gets Trending", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")

# remove Streamlit chrome/padding and make the iframe fill the browser window
st.markdown(
    """
<style>
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none !important;}
.block-container {padding:0 !important; max-width:100% !important;}
[data-testid="stAppViewContainer"], .stApp {background:#0A0F1C;}
iframe {height:100vh !important; width:100% !important; border:0; display:block;}
</style>""",
    unsafe_allow_html=True,
)

html = (Path(__file__).parent / "page.html").read_text(encoding="utf-8")
components.html(html, height=900, scrolling=True)
