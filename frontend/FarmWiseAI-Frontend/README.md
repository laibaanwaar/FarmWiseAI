# FarmWiseAI — Streamlit Frontend

Complete frontend for FarmWiseAI (agricultural AI assistant for Pakistan), built with **Streamlit + custom HTML/CSS**.
Sab pages ek hi app ke andar integrated hain — marketing site, auth flow, farmer app aur admin console.

---

## 1. Run kaisy karein

### Requirements
- Python **3.10+** (tested on 3.14)
- Internet sirf `pip install` ke liye (app khud bina API key chalta hai)

### Windows (PowerShell / CMD)

```powershell
cd FarmWiseAI-Frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Browser khud khul jayega: **http://localhost:8501**

### macOS / Linux

```bash
cd FarmWiseAI-Frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Custom port

```bash
streamlit run app.py --server.port 8510
```

> Agar `streamlit` command na mile to: `python -m streamlit run app.py`

---

## 2. Pages (saare 17)

| # | Page | URL | Code |
|---|------|-----|------|
| 1 | Marketing home | `/` | `farmwise/views/home.py` |
| 2 | About Us | `/about` | `farmwise/views/about.py` |
| 3 | Services | `/services` | `farmwise/views/services.py` |
| 4 | Crops | `/crops` | `farmwise/views/crops.py` |
| 5 | Create account | `/signup` | `farmwise/views/auth.py` |
| 6 | Verify email (6-digit OTP) | `/verify-email` | `farmwise/views/auth.py` |
| 7 | Resend code | `/resend-code` | `farmwise/views/auth.py` |
| 8 | Log in | `/login` | `farmwise/views/auth.py` |
| 9 | Forgot password | `/forgot-password` | `farmwise/views/auth.py` |
| 10 | Reset password | `/reset-password` | `farmwise/views/auth.py` |
| 11 | Farmer dashboard | `/app` | `farmwise/views/dashboard.py` |
| 12 | Crop assistant chat (EN + اردو) | `/chat` | `farmwise/views/chat.py` |
| 13 | Saved answers | `/saved-answers` | `farmwise/views/saved.py` |
| 14 | Admin overview | `/admin` | `farmwise/views/admin.py` |
| 15 | Users & roles | `/admin-users` | `farmwise/views/admin.py` |
| 16 | Audit activity | `/admin-audit` | `farmwise/views/admin.py` |
| 17 | Admin settings | `/admin-settings` | `farmwise/views/admin.py` |

### Flow
```
Home → Try the assistant → /chat (seed question, EN/اردو, crop select, source panel)
Signup → Verify email (OTP) → Dashboard → Ask → Chat
Login → Dashboard
Admin sidebar: Overview / Users & roles / Audit activity / Settings
```

Session ke andar login state, OTP email, chat history, saved answers aur admin actions (add user, role toggle, disable, delete) sab live kaam karte hain.

---

## 3. Folder structure

```
FarmWiseAI-Frontend/
├── app.py                  # entry point (page config, CSS, navigation)
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml         # light theme, lime primary color, headless server
├── assets/                 # (optional) apni photos yahan rakhein
└── farmwise/
    ├── pages.py            # 17 pages ka registry (st.Page)
    ├── routes.py           # URL slugs + href() / go()
    ├── theme.py            # colors, gradients, icons, media() helper
    ├── styles.css          # poora design system (~2100 lines)
    ├── components.py       # nav, hero, cards, footer, app nav, badges
    ├── data.py             # crops, services, users, audit, handbook KB
    ├── rag.py              # keyless retrieval engine + citations
    ├── state.py            # session state + audit logging
    └── views/
        ├── home.py
        ├── services.py
        ├── crops.py
        ├── about.py
        ├── auth.py         # 6 auth screens
        ├── dashboard.py
        ├── chat.py
        ├── saved.py
        └── admin.py        # 4 admin screens
```

---

## 4. Customize kaisy karein

### Colors / fonts
`farmwise/styles.css` ke top par CSS variables hain:

```css
--ink: #0E2118;      /* deep forest */
--lime: #C9F45B;     /* primary accent */
--limesoft: #EAF7C5;
--cream: #F8F7EF;    /* page background */
--paper: #FFFFFF;
```

Streamlit theme colors `.streamlit/config.toml` mein hain.

### Real photos (sample photos included)
`assets/` folder mein 13 AI-generated sample photos already shamil hain (hero, farmer, crops, irrigation, soil, disease, handbook).
Apni photos use karni hon to inhi names se replace kar dein (JPG/PNG/WebP). File na ho to gradient fallback chalta hai:

```
hero_field, field, farmer, portrait, handbook, wheat_close,
crop_wheat, crop_rice, crop_cotton, crop_sugarcane, crop_maize,
soil, water, disease
```

### Content badalna
- Crops, services, saved answers, recent questions: `farmwise/data.py`
- Handbook answers (EN + UR + citations): `farmwise/data.py` ki `KNOWLEDGE` list
- Admin demo users / audit entries: `farmwise/data.py` (`USERS`, `AUDIT`)

### Naye page add karna
1. `farmwise/views/` mein naya module banayein (e.g. `pricing.py` with `render()`).
2. `farmwise/routes.py` ke `PATHS` mein slug add karein.
3. `farmwise/pages.py` ke `registry()` mein `st.Page(...)` add karein.
Navigation links ke liye `href("slug")` use karein.

---

## 5. Notes

- **Koi API key required nahi.** Chat answers local handbook search (keyword + token scoring) se aate hain,
  har answer ke saath document, PDF page aur printed page ka citation hota hai.
- Yeh **frontend/demo** hai: auth aur admin actions session state mein hain (page refresh par reset).
  Production ke liye database + real auth backend jodna hoga.
- Bilingual: English aur Urdu (Nastaliq font) — chat ke right side se language toggle hota hai.
- Sample photos `assets/` mein included hain (AI-generated, royalty-free); chahein to apni real photos se replace kar dein.
- UI polish: hero par stats strip, "Every answer cited" trust section, card hover-lift + image zoom, fade-up entrance animations (reduced-motion respected).
- Tested: 17/17 pages render pass, desktop 1440px layout verified.
