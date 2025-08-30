# pages/3_Contribute.py
import os
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg, require_auth

st.set_page_config(page_title="Contribute · Mana Sambharalu", layout="wide")
set_blurred_bg()

if not DEMO_MODE and not require_auth():
    st.stop()

@st.cache_resource
def get_client():
    return SwechaAPIClient()
client = get_client()

st.title("➕ Contribute a Record")
st.markdown("Fill the details below to add a new festival record.")

# (keep your existing form code here exactly as you had it)
# ...
