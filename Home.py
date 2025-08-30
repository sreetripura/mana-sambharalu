# Home.py
import os, sys
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")
set_blurred_bg()  # after page_config

# Ensure local imports even if launched from elsewhere
sys.path.append(os.path.dirname(__file__))

# ---------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------
@st.cache_resource
def get_client():
    return SwechaAPIClient()

client = get_client()

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("otp_sent", False)

# Rehydrate token if present
if st.session_state.access_token and not st.session_state.authenticated:
    client.set_auth_token(st.session_state.access_token)
    me = client.read_users_me()
    if me:
        st.session_state.user = me
        st.session_state.authenticated = True

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;color:#d63384;'>మన సంబరాలు · Mana Sambharalu</h1>",
    unsafe_allow_html=True,
)
st.write(
    "A community-driven treasury of Indian festivals — explore, contribute, and preserve our cultural memories."
)

col1, col2 = st.columns([2, 1])

# ---------------------------------------------------------------------
# Navigation (left)
# ---------------------------------------------------------------------
with col1:
    st.markdown("### Navigation")

    if st.session_state.authenticated:
        # NOTE: we renamed the pages to 2_Explore.py and 3_Contribute.py
        st.page_link("pages/2_Explore.py", label="🔎 Explore Records →", width="stretch")
        st.page_link("pages/3_Contribute.py", label="➕ Contribute a Record →", width="stretch")
    else:
        st.info("Please log in to access **Explore** and **Contribute**.")
        st.button("🔒 Explore Records", disabled=True, help="Login required")
        st.button("🔒 Contribute a Record", disabled=True, help="Login required")

# ---------------------------------------------------------------------
# Account (right)
# ---------------------------------------------------------------------
with col2:
    st.markdown("### Account")
    tab_login, tab_signup = st.tabs(["Login", "Sign up"])

    # ---------------- Login ----------------
    with tab_login:
        if st.session_state.authenticated:
            name = (
                st.session_state.user.get("full_name")
                or st.session_state.user.get("name")
                or st.session_state.user.get("username")
                or "User"
            )
            st.success(f"Logged in as **{name}**")
            if st.button("Logout", type="secondary", width="stretch"):
                st.session_state.update(
                    {"authenticated": False, "access_token": None, "user": None}
                )
                st.rerun()
        else:
            with st.form("login"):
                uname = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX")
                pwd = st.text_input(
                    "Password", type="password", placeholder=("demo123" if DEMO_MODE else "••••••••")
                )
                ok = st.form_submit_button("Login", width="stretch")

            if ok:
                try:
                    res = client.login(uname.strip(), pwd)
                    if res and "access_token" in res:
                        st.session_state["access_token"] = res["access_token"]
                        client.set_auth_token(res["access_token"])
                        me = client.read_users_me()

                        # ✅ mark session authenticated (the bit you asked about)
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = me or {"username": uname.strip()}

                        st.success("Login successful. Use the links to navigate.")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or server rejected the request.")
                except RuntimeError as e:
                    st.error(str(e))

    # ---------------- Sign up (OTP flow) ----------------
    with tab_signup:
        if DEMO_MODE:
            st.info("DEMO mode: use any phone. OTP is **123456**.")
        phone = st.text_input("Phone (e.g., +91XXXXXXXXXX)", key="su_phone")

        if st.button("Send OTP", key="su_send", width="content"):
            resp = client.send_signup_otp(phone.strip())
            if resp and isinstance(resp, dict):
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
                created = client.verify_signup_otp(
                    phone=phone.strip(),
                    otp_code=otp.strip(),
                    name=name.strip(),
                    email=email.strip(),
                    password=pwd1,
                )
                if created:
                    st.success("Account created. Please log in from the Login tab.")
                    st.session_state["otp_sent"] = False
                else:
                    st.error("OTP verification failed.")
