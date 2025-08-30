import os, sys
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE, API_BASE

sys.path.append(os.path.dirname(__file__))

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")

@st.cache_resource
def get_client():  # cache across reruns
    return SwechaAPIClient()
client = get_client()

st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)

if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

st.markdown("<h1 style='text-align:center;color:#d63384;'>మన సంబరాలు · Mana Sambharalu</h1>", unsafe_allow_html=True)
st.caption(f"API: {API_BASE} · DEMO_MODE={'on' if DEMO_MODE else 'off'}")

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
        tab_login, tab_signup = st.tabs(["Login", "Sign up"])
        with tab_login:
            with st.form("login"):
                ident = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX or username/email")
                pwd = st.text_input("Password", type="password", placeholder=("demo123" if DEMO_MODE else "••••••••"))
                ok = st.form_submit_button("Login", use_container_width=True)
            if ok:
                res = client.login(ident, pwd)
                if res and isinstance(res, dict) and ("access_token" in res or res.get("token") or res.get("access")):
                    token = res.get("access_token") or res.get("token") or res.get("access")
                    st.session_state.access_token = token
                    client.set_auth_token(token)
                    me = client.read_users_me()
                    if me:
                        st.session_state.user = me
                        st.session_state.authenticated = True
                        st.success("Login successful.")
                        st.rerun()
                else:
                    details = ""
                    if isinstance(res, dict) and res.get("_details"):
                        d = res["_details"]
                        details = f" (status {d.get('status')} at `/{d.get('path')}` using {d.get('payload_keys')}: {str(d.get('body'))[:180]})"
                    elif isinstance(res, dict) and res.get("_error") == "not_found":
                        details = " · Endpoints not found on server."
                    st.error("Invalid credentials or server rejected the request." + details)
                    with st.expander("What to try"):
                        st.write("- Make sure you **have an account** on the Corpus API.")
                        st.write("- Try **+91… format** for phone, or try your **email/username**.")
                        st.write("- If you forgot the password, request a reset from an admin.")
        with tab_signup:
            st.info("If OTP signup is enabled for your number, use this to create an account; otherwise contact an admin.")
            with st.form("signup"):
                ph = st.text_input("Phone (e.g., +91XXXXXXXXXX)")
                send = st.form_submit_button("Send OTP", use_container_width=True)
            if send:
                r = client.send_signup_otp(ph)
                st.write(r if r else {"ok": False})
