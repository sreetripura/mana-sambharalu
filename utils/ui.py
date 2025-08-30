from __future__ import annotations
import streamlit as st

_BG_DEFAULT = "assets/bg/goddess_bg.png"

def set_blurred_bg(image_path: str = _BG_DEFAULT, *, blur_px: int = 18, opacity: float = 0.28) -> None:
    """Adds a full-screen blurred background image behind the app."""
    st.markdown(
        f"""
        <style>
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: url('{image_path}') center/cover no-repeat fixed;
            filter: blur({blur_px}px);
            opacity: {opacity};
            z-index: -1;   /* behind everything */
        }}
        /* soften containers a bit so text pops on the bg */
        .stApp [data-testid="stHeader"] {{ background: transparent; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def require_auth() -> bool:
    """Return True if logged in; otherwise show a hint + link back to Home."""
    if not st.session_state.get("authenticated"):
        st.error("Please log in from **Home** to continue.")
        st.page_link("Home.py", label="Go to Login →")
        return False
    return True
