import os, sys
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")

from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg

set_blurred_bg()

@st.cache_resource
def get_client():
    return SwechaAPIClient()
client = get_client()

# session state
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("otp_sent", False)

# rehydrate if token present
if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

# header
st.markdown(
    "<h1 style='text-align:center;color:#FF8C32;'>మన సంబరాలు · Mana Sambharalu</h1>",
    unsafe_allow_html=True,
)
st.write("A community-driven treasury of Indian festivals — explore, contribute, and preserve our cultural memories.")

if not st.session_state.authenticated:
    left, mid, right = st.columns([1,2,1])
    with mid:
        with st.container(border=True):
            st.markdown("### Account")
            tab_login, tab_signup, tab_token = st.tabs(["Login", "Sign up", "Paste token"])

            # ---- Login
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

            # ---- Sign up (UI only; backend may differ)
            with tab_signup:
                if DEMO_MODE:
                    st.info("DEMO mode: use any phone. OTP is **123456**.")
                phone = st.text_input("Phone (e.g., +91XXXXXXXXXX)", key="su_phone")
                if st.button("Send OTP", key="su_send", width="content"):
                    resp = getattr(client, "send_signup_otp", lambda *_: None)(phone.strip())
                    if isinstance(resp, dict):
                        st.session_state["otp_sent"] = True
                        st.success("OTP sent. Check your phone.")
                        if DEMO_MODE and resp.get("demo_otp"):
                            st.info(f"Demo OTP: **{resp['demo_otp']}**")
                    else:
                        st.error("Could not send OTP right now.")
                if st.session_state.get("otp_sent"):
                    with st.form("verify_signup"):
                        otp = st.text_input("OTP")
                        name = st.text_input("Full name")
                        email = st.text_input("Email")
                        pwd1 = st.text_input("Create password", type="password")
                        done = st.form_submit_button("Verify & Create account", width="stretch")
                    if done:
                        created = getattr(client, "verify_signup_otp", lambda **kwargs: None)(
                            phone=phone.strip(), otp_code=otp.strip(),
                            name=name.strip(), email=email.strip(), password=pwd1,
                        )
                        if created:
                            st.success("Account created. Please log in from the Login tab.")
                            st.session_state["otp_sent"] = False
                        else:
                            st.error("OTP verification failed.")

            # ---- Paste token
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
    col1, col2 = st.columns([2,1])
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
