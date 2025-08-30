# utils/ui.py
from __future__ import annotations
import base64, mimetypes, os
import streamlit as st

_BG_DEFAULT = "assets/bg/goddess_bg.png"  # change if your file name differs

def _data_uri(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith("data:"):
        return path
    # try as given
    if os.path.exists(path):
        mime, _ = mimetypes.guess_type(path)
        mime = mime or "image/png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    # try relative to repo root (when called from pages/)
    alt = os.path.join(os.getcwd(), path)
    if os.path.exists(alt):
        return _data_uri(alt)
    return None

def set_blurred_bg(image_path: str = _BG_DEFAULT, *, blur_px: int = 18, opacity: float = 0.30) -> None:
    uri = _data_uri(image_path)
    bg_css = (
        f'background: url("{uri}") center/cover no-repeat fixed;'
        if uri else 'background: radial-gradient(ellipse at top, #2b2b40, #0e0e13);'
    )
    st.markdown(
        f"""
        <style>
        .stApp::before {{
            content: "";
            position: fixed; inset: 0;
            {bg_css}
            filter: blur({blur_px}px);
            opacity: {opacity};
            z-index: -1;
        }}
        .stApp [data-testid="stHeader"] {{ background: transparent; }}
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
