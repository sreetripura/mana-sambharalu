# మన సంభరాలు · Mana Sambharalu

A community-driven Streamlit app to **explore** and **contribute** Indian festival records using the **Swecha Corpus API**.

<p align="center">
  <img alt="Home" src="assets/Screenshot%202025-08-28%20125720.png" width="800"><br/>
  <em>Home</em>
</p>

## ✨ Features
- 🔎 Explore corpus records (title, language, location, images)
- ➕ Contribute new records (metadata + optional media)
- 🔐 Login (demo mode supported)
- 🌗 Clean, responsive UI (Streamlit)

<p align="center">
  <img alt="Explore" src="assets/Screenshot%202025-08-28%20125608.png" width="800"><br/>
  <em>Explore</em>
</p>

<p align="center">
  <img alt="Contribute" src="assets/Screenshot%202025-08-28%20125652.png" width="800"><br/>
  <em>Contribute</em>
</p>

---

## 🧭 Project Layout
mana-sambharalu/
├─ Home.py # Landing + login
├─ pages/
│ ├─ 1_Explore.py # Browse/search records
│ └─ 2_Contribute.py # Create records + upload chunks
├─ utils/
│ └─ api_client.py # Swecha Corpus API wrapper
├─ config/
│ └─ settings.py # DEMO_MODE, API_BASE
├─ assets/ # Images used in README/UI
├─ requirements.txt
└─ pyproject.toml



## 🔧 Local Setup
```bash
# clone
git clone https://code.swecha.org/SreeTripura/mana-sambharalu.git
cd mana-sambharalu

# create & activate venv (Windows PowerShell)
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# install deps
pip install -r requirements.txt

# run the app
streamlit run Home.py


