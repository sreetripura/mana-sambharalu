# pages/1_Explore.py
from __future__ import annotations
import os, base64
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE

st.set_page_config(page_title="Explore · Mana Sambharalu", layout="wide")

# ---------- helpers ----------
ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
ASSETS = os.path.abspath(ASSETS)

def _data_uri(img_path: str) -> str | None:
    try:
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        ext = "png" if img_path.lower().endswith(".png") else "jpeg"
        return f"data:image/{ext};base64,{b64}"
    except Exception:
        return None

def set_blurred_bg(png_path: str, blur_px: int = 18):
    uri = _data_uri(png_path)
    if not uri:
        return
    st.markdown(
        f"""
        <style>
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: url("{uri}") center/cover no-repeat fixed;
            filter: blur({blur_px}px) brightness(0.55);
            z-index: -1;
        }}
        /* uniform thumbnail sizing for ALL st.image on this page */
        [data-testid="stImage"] img {{
            width: 100% !important;
            height: 260px !important;
            object-fit: cover !important;
            border-radius: 16px;
            box-shadow: 0 8px 22px rgba(0,0,0,.25);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------- auth-gate (Explore only when logged in on LIVE) ----------
if not DEMO_MODE and not st.session_state.get("authenticated"):
    st.title("🔒 Explore Telangana Festivals")
    st.info("Please login from **Home → Account** to view the festival list.")
    st.stop()

# background
set_blurred_bg(os.path.join(ASSETS, "bg", "explore_bg.png"))

st.title("🔎 Explore Telangana\nFestivals")

lang_tab = st.segmented_control(
    "Language", options=["Both", "English", "తెలుగు"], default="తెలుగు"
)

# Client (cached)
@st.cache_resource
def get_client():
    return SwechaAPIClient()

client = get_client()

# ---------- static catalog (local images) ----------
IMG_DIR = os.path.join(ASSETS, "festivals")

CATALOG = [
    {
        "slug": "bathukamma",
        "img": os.path.join(IMG_DIR, "bathukamma.jpg"),
        "en": "Bathukamma 🌼",
        "te": "బతుకమ్మ 🌼",
        "desc_en": "Flower festival celebrating life and sisterhood across Telangana.",
        "desc_te": "దసరా ముందు తొమ్మిది రోజులు జరుపుకునే తెలంగాణ పుష్పాల పండుగ.",
    },
    {
        "slug": "bonalu",
        "img": os.path.join(IMG_DIR, "bonalu.jpg"),
        "en": "Bonalu 🪔",
        "te": "బోనాలు 🪔",
        "desc_en": "Offerings to Mahankali with decorated pots, dances and drums.",
        "desc_te": "మహాంకాళి అమ్మవారికి అలంకరించిన బొనాలతో నివేదనలు, డప్పులతో నృత్యాలు.",
    },
    {
        "slug": "ugadi",
        "img": os.path.join(IMG_DIR, "ugadi.jpg"),
        "en": "Ugadi 🥭",
        "te": "ఉగాది 🥭",
        "desc_en": "Telugu New Year marked with ‘Ugadi Pachadi’—six tastes of life.",
        "desc_te": "తెలుగు నూతన సంవత్సరం. ‘ఉగాది పచ్చడి’తో జీవన ఆరు రుచుల సందేశం.",
    },
    {
        "slug": "sri_rama_navami",
        "img": os.path.join(IMG_DIR, "sri_rama_navami.jpg"),
        "en": "Sri Rama Navami 🏹",
        "te": "శ్రీరామనవమి 🏹",
        "desc_en": "Celebrates the birth of Lord Rama with kalyanam and prasadam.",
        "desc_te": "శ్రీరామ జన్మోత్సవం. కల్యాణం, ప్రత్యేక పూజలు, ప్రసాదం.",
    },
    {
        "slug": "vinayaka_chavithi",
        "img": os.path.join(IMG_DIR, "vinayaka_chavithi.jpg"),
        "en": "Vinayaka Chavithi 🐘",
        "te": "వినాయక చవితి 🐘",
        "desc_en": "Ganesh festival—install, worship and immerse Lord Ganesha.",
        "desc_te": "గణేశుని ప్రతిష్ఠించుకుని పూజలతో ఘనంగా జరుపుకునే పండుగ.",
    },
    {
        "slug": "navaratri",
        "img": os.path.join(IMG_DIR, "navaratri.jpg"),
        "en": "Navaratri ✨",
        "te": "నవరాత్రి ✨",
        "desc_en": "Nine nights of Devi worship, music and dance.",
        "desc_te": "దేవీ ఉపాసన, సంగీత నృత్యాలతో తొమ్మిది రాత్రుల మహోత్సవం.",
    },
]

# ---------- list UI ----------
for item in CATALOG:
    img_uri = _data_uri(item["img"])
    with st.container(border=True):
        if img_uri:
            st.image(item["img"], caption=None, width="stretch")
        else:
            st.caption("📷 Image not found")

        if lang_tab == "Both":
            st.markdown(f"## {item['en']}  \n### {item['te']}")
            st.write(item["desc_en"])
            st.write(item["desc_te"])
        elif lang_tab == "English":
            st.markdown(f"## {item['en']}")
            st.write(item["desc_en"])
        else:
            st.markdown(f"## {item['te']}")
            st.write(item["desc_te"])
