# pages/1_Explore.py
import streamlit as st
from utils.api_client import SwechaAPIClient

st.set_page_config(page_title="Explore Records", layout="wide")

@st.cache_resource
def get_client():
    return SwechaAPIClient()
client = get_client()

st.header("🔎 Explore Corpus Records")
q = st.text_input("Search (title, tags, etc.)", "")

items = []
try:
    items = client.search_records(q) if q else client.get_records()
except Exception as e:
    st.error(f"Fetch error: {e}")
    st.stop()

if not items:
    st.info("No records found. Try another search or add content in Contribute.")
else:
    for rec in items:
        title = rec.get("title") or rec.get("name_en") or rec.get("name_te") or f"Record #{rec.get('id','')}"
        st.subheader(title)

        meta = []
        cat = rec.get("category")
        if isinstance(cat, dict) and cat.get("name"):
            meta.append(f"Category: {cat['name']}")
        if "category_id" in rec:
            meta.append(f"category_id={rec['category_id']}")
        if "language" in rec:
            meta.append(f"Language: {rec['language']}")
        if "media_type" in rec:
            meta.append(f"Media: {rec['media_type']}")
        loc = rec.get("location")
        if isinstance(loc, dict) and loc.get("latitude") is not None and loc.get("longitude") is not None:
            meta.append(f"Location: {loc['latitude']},{loc['longitude']}")
        if meta:
            st.caption(" | ".join(meta))

        desc = rec.get("description") or rec.get("summary_en") or rec.get("summary_te")
        if desc:
            st.write(desc)

        img = rec.get("image_url") or rec.get("thumbnail_url")
        if img:
            st.image(img, width=520)

        for f in (rec.get("files") or rec.get("assets") or []):
            if isinstance(f, dict) and str(f.get("mime","")).startswith("image/") and f.get("url"):
                st.image(f["url"], width=520)

        st.divider()
