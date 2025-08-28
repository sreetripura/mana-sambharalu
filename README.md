# మన సంబరాలు • Mana Sambharalu

A community-driven treasury of Indian festivals built with **Streamlit** (frontend) and the **Swecha Corpus API** (backend).  
Users can explore public records and, after login, contribute new text/media with metadata (language, rights, location).  
The app supports a safe **DEMO mode** (offline) and a **LIVE mode** that persists to the real API.  
This repository contains a minimal client, chunked upload helpers, and a clean UI for Explore/Contribute.

---

## Screenshots

**Home**
![Home](assets/Screenshot%202025-08-28%20125720.png)

**Explore**
![Explore](assets/Screenshot%202025-08-28%20125608.png)

**Contribute**
![Contribute](assets/Screenshot%202025-08-28%20125652.png)

---

## Features

- Streamlit multi-page app: **Home**, **Explore**, **Contribute**.
- Login + token storage; optional OTP signup stubs (graceful fallbacks if endpoints differ).
- Create festival records (title/description/category/language/rights/location).
- **Chunked media upload** (images/audio/video/pdf), then server-side finalize.
- Defensive client: tries canonical endpoints first and compatible fallbacks if the API evolves.

---

## Architecture (Client–Server + OSaaS)

- **Client (this repo):** Streamlit UI + a thin Python client (`utils/api_client.py`).
- **Server (Swecha Corpus API):** Auth, categories, records, chunked object storage (**OSaaS**).
- **Key endpoints used**
  - `auth/login`, `auth/me` *(fallbacks: `login`, `me`)*
  - `categories`
  - `records`, `records/search`
  - `records/upload/chunk`, `records/upload/finalize`
  - Signup helpers: `auth/send-otp`, `auth/signup/verify`, `auth/resend-otp` *(optional; used if available)*

---

## Repository Layout

mana-sambharalu/
├─ assets/ # PNG screenshots used in README/UI
├─ config/
│ └─ settings.py # DEMO_MODE & API_BASE
├─ pages/
│ ├─ 1_Explore.py # Search & list records
│ └─ 2_Contribute.py # Create record + optional uploads
├─ utils/
│ └─ api_client.py # Swecha API client (auth, records, upload)
├─ Home.py # Landing page (links + login/logout)
├─ requirements.txt
├─ pyproject.toml 
