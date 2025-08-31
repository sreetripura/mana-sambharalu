# à°®à°¨ à°¸à°‚à°¬à°°à°¾à°²à± Â· Mana Sambharalu ðŸŽ‰

A community-driven treasury of Indian festivals â€” **explore**, **contribute**, and **preserve** our cultural memories.  
Built with Streamlit and a warm **orange / black / white / grey** theme ðŸ§¡ðŸ–¤ðŸ¤

---

## ðŸ”— Live App

- **Streamlit:** https://mana-sambharalu.streamlit.app

---

> In Demo Mode the app does not call a real API. Logging in simply unlocks the UI.

---

## ðŸ“¸ Screenshots

> If an image does not render on GitHub/GitLab, make sure the file exists and is **committed** at the same path.

<p align="center">
  <img src="assets/screenshots/home.png" alt="Home page" width="900">
</p>

<p float="left">
  <img src="assets/screenshots/explore1.png" alt="Explore grid (top)" width="49%">
  <img src="assets/screenshots/explore2.png" alt="Explore grid (bottom)" width="49%">
</p>

<p align="center">
  <img src="assets/screenshots/contribute.png" alt="Contribute form" width="900">
</p>

_Screenshot files live in **assets/screenshots/**. Replace them with your own images if you like (keep the same file names or update the paths above)._

---

## âœ¨ Features

- ðŸ” **Login / Sign-up (Demo)** â€“ simple session state; â€œdemo123â€ unlocks Explore & Contribute.
- ðŸ”Ž **Explore** â€“ bilingual (English/à°¤à±†à°²à±à°—à±) festival cards with **uniform image sizes**.
- âž• **Contribute** â€“ add records (title, language, rights, geotags, demo media preview).
- ðŸ§¡ **Theme** â€“ orange headline accents, dark surface, soft card shadows, rounded corners.
- ðŸŒ **Background** â€“ blurred Devi image applied globally via a small CSS helper.

---

## ðŸ§± Tech Stack

- **Python 3.10+**, **Streamlit**
- Light CSS via `st.markdown` for background & cards
- Packaging with **pyproject.toml** (works great with `uv`)

---

## ðŸ“‚ Project Structure (partial)

assets/
bg/
goddess_bg.png
festivals/
home.png
explore1.png
explore2.png
contribute.png
config/
settings.py
pages/
1_Dashboard.py
2_Explore.py
3_Contribute.py
utils/
api_client.py
ui.py
Home.py
pyproject.toml

yaml
Copy code

---

## â–¶ï¸ Run Locally

### Using uv

```bash
uv sync
uv run streamlit run Home.py
Using pip (virtual env)
bash
Copy code
python -m venv .venv
# Windows
. .venv/Scripts/activate
# macOS/Linux
# source .venv/bin/activate

pip install -r <(uv pip compile pyproject.toml)  # or just install packages from pyproject with pip/uv
streamlit run Home.py
ðŸ‘¥ Team

Sree Tripura â€” https://code.swecha.org/SreeTripura

Vaishnavi Bussa â€” https://code.swecha.org/vaishnavibussa

Gayathri Kodipaka â€” https://code.swecha.org/Gayathrikodipaka

Deekshitha M â€” https://code.swecha.org/DeekshithaM

Sudhamsh â€” https://code.swecha.org/Sudhamsh22



```
