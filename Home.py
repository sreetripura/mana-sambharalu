# Home.py
import os, sys
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")
set_blurred_bg()

sys.path.append(os.path.dirname(__file__))

@st.cache_resource
def get_client():
    return SwechaAPIClient()

client = get_client()

# session
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("otp_sent", False)

# rehydrate
if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

# heading
st.markdown(
    "<h1 style='text-align:center;color:#ff8c32;'>మన సంబరాలు · Mana Sambharalu</h1>",
    unsafe_allow_html=True,
)
st.write("A community-driven treasury of Indian festivals — explore, contribute, and preserve our cultural memories.")

# centered auth box
if not st.session_state.authenticated:
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        st.markdown("### Account")
        tab_login, tab_signup = st.tabs(["Login", "Sign up"])

        # Login
        with tab_login:
            with st.form("login"):
                uname = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX")
                pwd = st.text_input("Password", type="password", placeholder=("••••••••"))
                ok = st.form_submit_button("Login", width="stretch")
            if ok:
                try:
                    res = client.login(uname.strip(), pwd)
                    if res and "access_token" in res:
                        st.session_state["access_token"] = res["access_token"]
                        client.set_auth_token(res["access_token"])
                        me = client.read_users_me()
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = me or {"username": uname.strip()}
                        st.success("Login successful.")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or server rejected the request.")
                except RuntimeError as e:
                    st.error(str(e))

        # Sign up (UI only; requires backend endpoints)
        with tab_signup:
            phone = st.text_input("Phone (e.g., +91XXXXXXXXXX)", key="su_phone")
            send = st.button("Send OTP", key="su_send", type="secondary")
            if send:
                st.info("Signup/OTP endpoints must be enabled on the API. Ask the backend team to expose them.")

else:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Navigation")
        st.page_link("pages/2_Explore.py", label="🔎 Explore Records →", width="stretch")
        st.page_link("pages/3_Contribute.py", label="➕ Contribute a Record →", width="stretch")
    with col2:
        st.markdown("### Account")
        name = (
            st.session_state.user.get("full_name")
            or st.session_state.user.get("name")
            or st.session_state.user.get("username")
            or "User"
        )
        st.success(f"Logged in as **{name}**")
        if st.button("Logout", type="secondary", width="stretch"):
            st.session_state.update({"authenticated": False, "access_token": None, "user": None})
            st.rerun()
