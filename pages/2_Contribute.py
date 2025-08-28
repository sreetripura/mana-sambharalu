# pages/2_Contribute.py
import uuid
import streamlit as st
from utils.api_client import SwechaAPIClient

st.set_page_config(page_title="Contribute", layout="wide")

@st.cache_resource
def get_client():
    return SwechaAPIClient()
client = get_client()

# Require login
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("access_token", None)
if not st.session_state.authenticated:
    st.error("Please login from Home to contribute.")
    st.stop()

client.set_auth_token(st.session_state.access_token)

st.header("➕ Contribute a New Record")

# Categories
cats = client.get_categories()
id_by_name, name_options = {}, []
for c in cats:
    cid = c.get("id")
    nm = c.get("name") or c.get("title") or f"Category {cid}"
    if cid is not None:
        id_by_name[nm] = cid
        name_options.append(nm)

with st.form("record_form"):
    title = st.text_input("Title *")
    description = st.text_area("Description *", height=120)

    if name_options:
        category_name = st.selectbox("Category *", name_options, index=0, placeholder="Select a category")
        category_id = id_by_name.get(category_name)
    else:
        st.warning("No categories available from the server. Enter a Category ID manually.")
        category_id = st.number_input("Category ID * (temporary fallback)", min_value=1, step=1)

    language = st.selectbox("Language", ["telugu", "hindi", "english", "other"], index=0)
    release_rights = st.selectbox("Release Rights", ["creator", "family_or_friend", "downloaded"], index=0)
    tags_csv = st.text_input("Tags (comma-separated)")
    c1, c2 = st.columns(2)
    with c1: lat = st.text_input("Latitude (optional)")
    with c2: lon = st.text_input("Longitude (optional)")
    files = st.file_uploader("Upload files", accept_multiple_files=True)
    submit = st.form_submit_button("Create Record", use_container_width=True)

if submit:
    if not title or not description or not category_id:
        st.error("Please fill Title, Description, and a valid Category (or Category ID).")
        st.stop()

    payload = {
        "title": title.strip(),
        "description": description.strip(),
        "category_id": int(category_id),
        "language": language,
        "release_rights": release_rights,
        "tags": [t.strip() for t in tags_csv.split(",") if t.strip()],
    }
    try:
        lat_v = float(lat) if lat else None
        lon_v = float(lon) if lon else None
        if lat_v is not None and lon_v is not None:
            payload["location"] = {"latitude": lat_v, "longitude": lon_v}
    except ValueError:
        st.warning("Ignoring invalid location (must be numeric).")

    with st.spinner("Creating metadata…"):
        created = client.create_record(payload)

    if not created:
        st.error("Failed to create record metadata.")
        st.stop()

    st.success(f"Record created with id={created.get('id')}")

    if files:
        upload_uuid = str(uuid.uuid4())
        all_ok = True
        for f in files:
            content = f.read()
            chunks = client.chunk_file(content, chunk_size=1024 * 1024)  # 1 MiB
            total = len(chunks)
            for i, ch in enumerate(chunks):
                ok = client.upload_file_chunk(
                    upload_uuid=upload_uuid, filename=f.name, chunk_bytes=ch,
                    chunk_index=i, total_chunks=total, mime=f.type or "application/octet-stream",
                )
                if not ok:
                    all_ok = False
                    st.error(f"Chunk {i+1}/{total} failed for {f.name}.")
                    break
        if all_ok:
            st.success("All files uploaded successfully.")
    else:
        st.info("No files chosen; only metadata was created.")
