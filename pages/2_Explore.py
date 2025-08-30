from __future__ import annotations
import os
import streamlit as st
from utils.ui import set_blurred_bg, require_auth
from config.settings import ALLOW_ANON_EXPLORE

st.set_page_config(page_title="Explore · Mana Sambharalu", layout="wide")
set_blurred_bg()

if not ALLOW_ANON_EXPLORE and not require_auth():
    st.stop()

st.title("🔎 Explore Telangana\nFestivals")

# (keep the rest of your Explore page content/images as you already have)
