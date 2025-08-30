# Home.py — header must be first
import os, sys
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

import streamlit as st
from utils.ui import set_blurred_bg
from utils.api_client import SwechaAPIClient, DEMO_MODE

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")
set_blurred_bg()

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

st.markdown(
    "<h1 style='text-align:center;color:#ff8c32;'>మన సంబరాలు · Mana Sambharalu</h1>",
    unsafe_allow_html=True,
)
st.write("A community-driven treasury of Indian festivals — explore, contribute, and preserve our cultural memories.")

# ---------------- Not logged in: show centered auth box ----------------
if not st.session_state.authenticated:
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        st.markdown("### Account")
        tab_login, tab_signup = st.tabs(["Login", "Sign up"])

        with tab_login:
            with st.form("login"):
                uname = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX")
                pwd = st.text_input("Password", type="password", placeholder=("demo123" if DEMO_MODE else "••••••••"))
                ok = st.form_submit_button("Login", width="stretch")
            if ok:
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

        with tab_signup:
            if DEMO_MODE:
                st.info("Demo sign-up: OTP is **123456**.")
            phone = st.text_input("Phone (+91…)", key="su_phone")
            if st.button("Send OTP", key="su_send"):
                resp = client.send_signup_otp(phone.strip())
                if resp:
                    st.session_state["otp_sent"] = True
                    st.success("OTP sent.")
                    if DEMO_MODE and resp.get("demo_otp"):
                        st.caption(f"Demo OTP: **{resp['demo_otp']}**")
                else:
                    st.error("Could not send OTP.")
            if st.session_state.get("otp_sent"):
                with st.form("verify_signup"):
                    otp = st.text_input("OTP")
                    name = st.text_input("Full name")
                    email = st.text_input("Email")
                    pwd1 = st.text_input("Create password", type="password", value="demo123" if DEMO_MODE else "")
                    done = st.form_submit_button("Verify & Create account", width="stretch")
                if done:
                    ok = client.verify_signup_otp(
                        phone=phone.strip(), otp_code=otp.strip(),
                        name=name.strip(), email=email.strip(), password=pwd1
                    )
                    if ok:
                        st.success("Account created. Please log in from the Login tab.")
                        st.session_state["otp_sent"] = False
                    else:
                        st.error("OTP verification failed.")
else:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Navigation")
        st.page_link("pages/2_Explore.py", label="🔎 Explore Records →", width="stretch")
        st.page_link("pages/3_Contribute.py", label="➕ Contribute a Record →", width="stretch")
    with col2:
        st.markdown("### Account")
        name = (st.session_state.user.get("full_name") or
                st.session_state.user.get("name") or
                st.session_state.user.get("username") or "User")
        st.success(f"Logged in as **{name}**")
        if st.button("Logout", type="secondary", width="stretch"):
            st.session_state.update({"authenticated": False, "access_token": None, "user": None})
            st.rerun()
