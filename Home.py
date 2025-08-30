import os, sys
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg, center_wrapper

# Ensure imports even if launched from elsewhere
sys.path.append(os.path.dirname(__file__))

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")
set_blurred_bg()

@st.cache_resource
def get_client():
    return SwechaAPIClient()

client = get_client()

# Session state
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("otp_sent", False)

# Rehydrate token
if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

st.markdown(
    "<h1 style='text-align:center;color:#ff8c32;'>మన సంబరాలు · Mana Sambharalu</h1>",
    unsafe_allow_html=True,
)
st.write("A community-driven treasury of Indian festivals — explore, contribute, and preserve our cultural memories.")

# Center the login/signup UI
if not st.session_state.authenticated:
    left, mid, right = center_wrapper(1, 2, 1)
    with mid:
        st.markdown("### Account")
        tab_login, tab_signup, tab_token = st.tabs(["Login", "Sign up", "Paste token"])

        # Login (password) — may fail if backend blocks password login
        with tab_login:
            with st.form("login"):
                uname = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX")
                pwd = st.text_input("Password", type="password", placeholder=("demo123" if DEMO_MODE else "••••••••"))
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
                        st.success("Login successful."); st.rerun()
                    else:
                        st.error("Invalid credentials or server rejected the request.")
                except RuntimeError as e:
                    st.error(str(e))

        # Sign up via OTP (only works if backend supports these endpoints)
        with tab_signup:
            if DEMO_MODE:
                st.info("DEMO mode: use any phone. OTP is **123456**.")
            phone = st.text_input("Phone (e.g., +91XXXXXXXXXX)", key="su_phone")
            if st.button("Send OTP", key="su_send", width="content"):
                resp = client.send_login_otp(phone.strip())
                if resp and isinstance(resp, dict):
                    st.session_state["otp_sent"] = True
                    st.success("OTP sent. Check your phone.")
                    if DEMO_MODE and resp.get("demo_otp"):
                        st.info(f"Demo OTP: **{resp['demo_otp']}**")
                else:
                    st.error("Could not send OTP right now.")
            if st.session_state.get("otp_sent"):
                with st.form("verify_login"):
                    otp = st.text_input("OTP")
                    done = st.form_submit_button("Verify & Log in", width="stretch")
                if done:
                    res = client.verify_login_otp(phone.strip(), otp.strip())
                    if res and "access_token" in res:
                        st.session_state["access_token"] = res["access_token"]
                        client.set_auth_token(res["access_token"])
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = client.read_users_me() or {"phone": phone.strip()}
                        st.success("Logged in."); st.rerun()
                    else:
                        st.error("OTP verification failed.")

        # Paste token (rock-solid fallback)
        with tab_token:
            st.caption("If the API team gives you a bearer token, paste it here.")
            tkn = st.text_input("Bearer token", type="password")
            if st.button("Use token", type="primary"):
                if tkn and client.set_token_and_verify(tkn):
                    st.session_state["access_token"] = tkn
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = client.read_users_me() or {}
                    st.success("Token accepted."); st.rerun()
                else:
                    st.error("Token invalid or profile fetch failed.")

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
