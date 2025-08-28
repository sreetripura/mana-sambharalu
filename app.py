import streamlit as st
from utils.api_client import SwechaAPIClient

st.set_page_config(page_title="మన సంబరాలు - Mana Sambharalu", layout="wide")

@st.cache_resource
def get_client():
    return SwechaAPIClient()

client = get_client()

# ---- session state ----
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("signup_step", 1)
st.session_state.setdefault("signup_phone", "")

# rehydrate
if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

st.markdown("<h1 style='text-align:center;color:#d63384;'>మన సంబరాలు 🎉</h1>", unsafe_allow_html=True)

# ---- sidebar auth ----
with st.sidebar:
    if st.session_state.authenticated:
        st.success(f"Logged in: {st.session_state.user.get('full_name','User')}")
        if st.button("Logout", use_container_width=True):
            st.session_state.update({"authenticated": False, "access_token": None, "user": None})
            st.rerun()
    else:
        st.info("Not logged in")

# ---- tabs: login / sign up ----
tab_login, tab_signup = st.tabs(["🔐 Login", "🆕 Sign Up"])

with tab_login:
    st.subheader("Login")
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
        pwd = st.text_input("Password", type="password", placeholder="demo mode password: demo123")
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
                st.success("Login successful! Redirecting…")
                st.rerun()
        else:
            st.error("Invalid credentials.")

with tab_signup:
    st.subheader("Create an account")
    if st.session_state.signup_step == 1:
        with st.form("send_otp"):
            p = st.text_input("Phone Number", value=st.session_state.signup_phone, placeholder="+91XXXXXXXXXX")
            s = st.form_submit_button("Send OTP", use_container_width=True)
        if s:
            if client.send_signup_otp(p):
                st.session_state.signup_phone = p
                st.session_state.signup_step = 2
                st.success("OTP sent. Check your phone.")
            else:
                st.error("Failed to send OTP.")
    else:
        with st.form("verify_otp"):
            st.text_input("Phone Number", value=st.session_state.signup_phone, disabled=True)
            otp = st.text_input("OTP Code", placeholder="Enter OTP")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            pwd1 = st.text_input("Password", type="password")
            pwd2 = st.text_input("Confirm Password", type="password")
            consent = st.checkbox("I agree to the terms and conditions")
            v = st.form_submit_button("Verify & Create Account", use_container_width=True)
        if v:
            if pwd1 != pwd2:
                st.error("Passwords do not match.")
            elif len(pwd1) < 6:
                st.error("Password must be at least 6 characters.")
            elif not consent:
                st.error("Please accept the terms.")
            else:
                ok2 = client.verify_signup_otp(st.session_state.signup_phone, otp, name, email, pwd1, consent)
                if ok2:
                    st.success("Account created! Please log in.")
                    st.session_state.signup_step = 1
                else:
                    st.error("OTP verification failed.")

st.markdown("---")

# ---- main page ----
if st.session_state.authenticated:
    st.header("🎊 Explore Festivals")
    q = st.text_input("🔎 Search Festivals", "")
    items = client.search_festivals(q) if q else client.get_festivals()

    if not items:
        st.info("No festivals found. Try another search term.")
    else:
        for f in items:
            with st.container():
                st.subheader(f"{f.get('name_te','')} / {f.get('name_en','')}")
                st.caption(f"Month: {f.get('month','')} | Regions: {', '.join(f.get('regions',[]))}")
                st.write(f.get('summary_te') or f.get('summary_en') or "")
                if f.get('image_url'):
                    st.image(f['image_url'], width=520)
else:
    st.info("Please log in or sign up to continue.")
