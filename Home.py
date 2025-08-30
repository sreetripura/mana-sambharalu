import os, sys
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg, center_column

st.set_page_config(page_title="మన సంబరాలు · Home", layout="wide")
set_blurred_bg()  # blurred goddess bg

# make relative imports work when launched from elsewhere
sys.path.append(os.path.dirname(__file__))

@st.cache_resource
def get_client(): return SwechaAPIClient()
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

st.markdown(
    "<h1 style='text-align:center;color:#f97316;'>మన సంబరాలు · Mana Sambharalu</h1>",
    unsafe_allow_html=True,
)
st.write(
    "<div style='text-align:center;opacity:.85'>A community-driven treasury of Indian festivals — explore, contribute, and preserve.</div>",
    unsafe_allow_html=True,
)

# ---------- centered login / signup ----------
c = center_column(2)
with c:
    box = st.container(border=True)
    with box:
        st.markdown("### Account")
        tab_login, tab_signup = st.tabs(["Login", "Sign up"])

        with tab_login:
            if st.session_state.authenticated:
                name = (
                    st.session_state.user.get("full_name")
                    or st.session_state.user.get("name")
                    or st.session_state.user.get("username")
                    or "User"
                )
                st.success(f"Logged in as **{name}**")

                st.page_link("pages/1_Dashboard.py", label="Go to Dashboard →", width="stretch")
                if st.button("Logout", type="secondary", key="logout", help="Sign out", use_container_width=True):
                    st.session_state.update({"authenticated": False, "access_token": None, "user": None})
                    st.rerun()
            else:
                with st.form("login"):
                    uname = st.text_input("Phone / Username", placeholder="+91XXXXXXXXXX")
                    pwd   = st.text_input("Password", type="password", placeholder=("demo123" if DEMO_MODE else "••••••••"))
                    ok    = st.form_submit_button("Login", use_container_width=True)

                if ok:
                    try:
                        res = client.login(uname.strip(), pwd)
                        if res and "access_token" in res:
                            st.session_state["access_token"] = res["access_token"]
                            client.set_auth_token(res["access_token"])
                            me = client.read_users_me()
                            st.session_state["authenticated"] = True
                            st.session_state["user"] = me or {"username": uname.strip()}
                            st.rerun()
                        else:
                            st.error("Invalid credentials or server rejected the request.")
                    except RuntimeError as e:
                        st.error(str(e))

        with tab_signup:
            if DEMO_MODE:
                st.info("DEMO mode: you can use any phone. OTP is **123456**.")
            phone = st.text_input("Phone (e.g., +91XXXXXXXXXX)", key="su_phone")
            if st.button("Send OTP", key="su_send", use_container_width=False):
                resp = client.send_signup_otp(phone.strip())
                if resp and isinstance(resp, dict):
                    st.session_state["otp_sent"] = True
                    st.success("OTP sent. Check your phone.")
                    if DEMO_MODE and resp.get("demo_otp"): st.info(f"Demo OTP: **{resp['demo_otp']}**")
                else:
                    st.error("Could not send OTP right now.")
            if st.session_state.get("otp_sent"):
                with st.form("verify_signup"):
                    otp   = st.text_input("OTP")
                    name  = st.text_input("Full name")
                    email = st.text_input("Email")
                    pwd1  = st.text_input("Create password", type="password")
                    done  = st.form_submit_button("Verify & Create account", use_container_width=True)
                if done:
                    created = client.verify_signup_otp(
                        phone=phone.strip(), otp_code=otp.strip(),
                        name=name.strip(), email=email.strip(), password=pwd1
                    )
                    if created:
                        st.success("Account created. Please log in from the Login tab.")
                        st.session_state["otp_sent"] = False
                    else:
                        st.error("OTP verification failed.")
