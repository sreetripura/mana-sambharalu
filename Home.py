# Home.py
import os, sys
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE

# ensure local imports even if launched from elsewhere
sys.path.append(os.path.dirname(__file__))

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")

@st.cache_resource
def get_client(mode_flag=DEMO_MODE):  # cache busts if mode changes
    return SwechaAPIClient()
client = get_client()

# session state
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)

# rehydrate token
if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

st.markdown("<h1 style='text-align:center;color:#d63384;'>మన సంబరాలు · Mana Sambharalu</h1>", unsafe_allow_html=True)
st.write("A community-driven treasury of Indian festivals. Explore, contribute, and preserve.")

col1, col2 = st.columns([2, 1])

with col1:
    st.page_link("pages/1_Explore.py", label="Explore Records →", use_container_width=True)
    st.page_link("pages/2_Contribute.py", label="Contribute a Record →", use_container_width=True)

with col2:
    st.markdown("### Account")
    if st.session_state.authenticated:
        st.success(f"Logged in as **{st.session_state.user.get('full_name','User')}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.update({"authenticated": False, "access_token": None, "user": None})
            st.rerun()
    else:
        with st.form("login"):
            phone = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX")
            pwd = st.text_input("Password", type="password", placeholder=("demo123" if DEMO_MODE else "••••••••"))
            ok = st.form_submit_button("Login", use_container_width=True)
        if ok:
            res = client.login_for_access_token(phone, pwd)
            if res and "access_token" in res:
                st.session_state.access_token = res["access_token"]
                client.set_auth_token(res["access_token"])
                me = client.read_users_me()
                if me:
                    st.session_state.user = me
                    st.session_state.authenticated = True
                    st.success("Login successful. Use the links to navigate.")
            else:
                st.error("Invalid credentials.")
