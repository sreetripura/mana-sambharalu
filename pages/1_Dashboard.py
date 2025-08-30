import streamlit as st
from utils.ui import set_blurred_bg, require_auth

st.set_page_config(page_title="Dashboard · Mana Sambharalu", layout="wide")
set_blurred_bg()

if not require_auth(): st.stop()

st.markdown("## Dashboard")
st.page_link("pages/2_Explore.py",   label="🔎 Explore Records →",  width="stretch")
st.page_link("pages/3_Contribute.py", label="➕ Contribute a Record →", width="stretch")
