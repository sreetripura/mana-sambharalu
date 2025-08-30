# pages/2_Explore.py
from __future__ import annotations
import os
import streamlit as st
from utils.api_client import SwechaAPIClient, DEMO_MODE
from utils.ui import set_blurred_bg

st.set_page_config(page_title="Explore · Mana Sambharalu", layout="wide")
set_blurred_bg()  # blurred goddess background

st.markdown(
    """
    <style>
    /* Uniform thumbnails for ALL images on this page */
    [data-testid="stImage"] img {
        width: 100% !important;         /* fill the card width */
        aspect-ratio: 16/9 !important;  /* <- change to 1/1 for square tiles */
        height: auto !important;
        object-fit: cover !important;   /* crop to fit, no distortion */
        border-radius: 14px;
        box-shadow: 0 8px 22px rgba(0,0,0,.25);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔎 Explore Telangana\nFestivals")

# ------------------------------------------------------------------
# Static catalog (local images)
# ------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
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

# ------------------------------------------------------------------
# Responsive 2-column grid so widths match
# ------------------------------------------------------------------
cols = st.columns(2, gap="large")

for i, item in enumerate(CATALOG):
    with cols[i % 2]:
        with st.container(border=True):
            st.image(item["img"], caption=None, width="stretch")  # width is uniform via column
            # Names + short descriptions
            st.markdown(f"## {item['en']}  \n### {item['te']}")
            st.write(item["desc_en"])
            st.write(item["desc_te"])
