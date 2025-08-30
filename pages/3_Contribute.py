from __future__ import annotations
import os
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg, require_auth

st.set_page_config(page_title="Contribute · Mana Sambharalu", layout="wide")
set_blurred_bg()

@st.cache_resource
def get_client():
    return SwechaAPIClient()

client = get_client()

# LIVE must be authenticated
if not DEMO_MODE and not require_auth():
    st.stop()

st.title("➕ Contribute a Record")
st.markdown("Fill the details below to add a new festival record.")

# Categories
@st.cache_data(ttl=600)
def _get_categories():
    cats = client.get_categories() or []
    if not cats:
        cats = [{"id": 1, "name": "Festivals"}]
    return cats

categories = _get_categories()
cat_names = [c["name"] for c in categories]
cat_id_by_name = {c["name"]: c["id"] for c in categories}

with st.form("contribute_form", enter_to_submit=False):
    col_a, col_b = st.columns([2, 1])
    with col_a:
        title = st.text_input("Title*", placeholder="e.g., Bathukamma Procession")
        description = st.text_area("Description*", height=140,
                                   placeholder="A short description of the festival moment, significance, etc.")
        language = st.text_input("Language", value="telugu")
    with col_b:
        cat_name = st.selectbox("Category", options=cat_names, index=0)
        rights = st.selectbox(
            "Release rights",
            options=["CC BY-SA 4.0", "CC BY 4.0", "Public Domain (CC0)", "All rights reserved"],
            index=0,
        )
        lat = st.number_input("Latitude (optional)", step=0.000001, format="%.6f")
        lon = st.number_input("Longitude (optional)", step=0.000001, format="%.6f")

    st.divider()
    uploads = st.file_uploader(
        "Photos / media (optional — media upload is demo-only for now on this UI)",
        type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "wav", "mp3"],
        accept_multiple_files=True,
        help="You can attach images or short clips. In DEMO mode we just preview them.",
    )

    submitted = st.form_submit_button("Submit record", width="stretch")

if submitted:
    problems = []
    if not title.strip(): problems.append("Title is required.")
    if not description.strip(): problems.append("Description is required.")
    if problems:
        st.error(" ".join(problems)); st.stop()

    with st.spinner("Creating record…"):
        rec = client.create_record(
            title=title.strip(), description=description.strip(),
            category_id=cat_id_by_name.get(cat_name, 1),
            language=language.strip() or "telugu",
            release_rights=rights, latitude=(lat or None), longitude=(lon or None),
        )

    if not rec:
        st.error("Could not create the record. Please try again."); st.stop()

    rec_id = rec.get("id") if isinstance(rec, dict) else None
    st.success(f"Record created successfully! {('(ID: ' + str(rec_id) + ')') if rec_id else ''}")

    if uploads:
        if DEMO_MODE:
            st.info("Demo mode: showing previews (no real upload).")
            cols = st.columns(3)
            for i, f in enumerate(uploads):
                with cols[i % 3]:
                    if f.type.startswith("image/"):
                        st.image(f.read(), caption=f.name, width="stretch")
                    else:
                        st.caption(f"Attached: {f.name} ({f.type})")
        else:
            st.warning("Media uploads vary across API deployments. This UI currently saves metadata only.")

    st.toast("Thanks for your contribution!", icon="🎉")
    st.balloons()
