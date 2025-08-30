# utils/ui.py
from __future__ import annotations
import os
import streamlit as st

_BG_DEFAULT = "assets/bg/goddess_bg.png"  # put your image here

def set_blurred_bg(image_path: str = _BG_DEFAULT, *, blur_px: int = 18, opacity: float = 0.28) -> None:
    exists = os.path.exists(image_path)
    bg_css = (
        f"background: url('{image_path}') center/cover no-repeat fixed;"
        if exists else
        "background: linear-gradient(135deg,#ffffff,#f5f5f5) fixed;"
    )
    st.markdown(
        f"""
        <style>
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            {bg_css}
            filter: blur({blur_px}px);
            opacity: {opacity};
            z-index: -1;
        }}
        /* orange/black/gray accents */
        h1, h2, h3 {{ color: #ff8c32 !important; }}
        .stButton>button {{ background:#ff8c32; color:#fff; border:0; }}
        .stButton>button:hover {{ filter: brightness(0.95); }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def require_auth() -> bool:
    if not st.session_state.get("authenticated"):
        st.error("Please log in from **Home** to continue.")
        st.page_link("Home.py", label="Go to Login →")
        return False
    return True
