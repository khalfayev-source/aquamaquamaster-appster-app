import os
import io
from datetime import datetime

import streamlit as st
import pandas as pd

from streamlit_js_eval import get_geolocation

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# =========================
# CONFIG
# =========================
SHEET_ID = "1PO8vl6lVCio9lHgFrZFQ9Sgz6XRbVOWYyh8FMZzaM9E"
DRIVE_FOLDER_ID = "1SgXAWg6xxyq4L_UmFiaQeo8yE5bCZVXu"

# Worksheet adı (Sheets içində tab)
WORKSHEET_NAME = "Data"

# Səliqəli, sabit kolon ardıcıllığı
CANON_COLS = [
    "Tarix",
    "Mağaza",
    "Rayon",
    "Tip",
    "Sahibkar",
    "Telefon",
    "Satıcı Var?",
    "Həcm",
    "Latitude",
    "Longitude",
    "Şəkil Linki",
    "Qeyd",
]

# key.json faylının yolu (səndə upload olunub / repo-da olacaq)
SERVICE_ACCOUNT_FILE = "key.json"

# =========================
# AUTH (Sheets + Drive)
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_clients():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    drive = build("drive", "v3", credentials=creds)
    return gc, drive

def ensure_worksheet(gc):
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=len(CANON_COLS))

    # Header yoxdursa yaz
    current = ws.row_values(1)
    if current != CANON_COLS:
        # 1-ci sətri CANON_COLS elə
        ws.update("A1", [CANON_COLS])

    return ws

def upload_image_to_drive(drive, image_bytes: bytes, filename: str) -> str:
    """
    Şəkli Drive folder-ə upload edir, public view link qaytarır.
    """
    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype="image/jpeg", resumable=False)

    file_metadata = {
        "name": filename,
        "parents": [DRIVE_FOLDER_ID]
    }

    created = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = created["id"]

    # Link açıq olsun (istəsən bunu söndürə bilərik)
    drive.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"

def append_row(ws, row_dict: dict):
    # CANON_COLS ardıcıllığı ilə list yaradırıq
    row = [row_dict.get(c, "") for c in CANON_COLS]
    ws.append_row(row, value_input_option="USER_ENTERED")

# =========================
# UI
# =========================
st.set_page_config(page_title="Aquamaster Cənub (Prod)", page_icon="💧")
st.title("💧 Aquamaster Cənub (Prod)")

# session init (widget key-ləri)
st.session_state.setdefault("lat_input", "")
st.session_state.setdefault("lng_input", "")
st.session_state.setdefault("geo_pending", False)

# ---- GEO BLOCK ----
st.markdown("### 📍 Məkan")
geo_click = st.button("📍 MƏKANI TƏYİN ET", use_container_width=True)

loc = None
if geo_click or st.session_state.get("geo_pending", False):
    st.session_state["geo_pending"] = True
    loc = get_geolocation()

# loc parse → birbaşa widget state-ə yaz (lat_input / lng_input)
if isinstance(loc, dict):
    coords = loc.get("coords") or {}
    lat = coords.get("latitude", loc.get("latitude"))
    lng = coords.get("longitude", loc.get("longitude"))

    if lat is not None and lng is not None:
        st.session_state["lat_input"] = f"{float(lat):.6f}"
        st.session_state["lng_input"] = f"{float(lng):.6f}"
        st.session_state["geo_pending"] = False

if st.session_state.get("lat_input") and st.session_state.get("lng_input"):
    st.success(f"Tapıldı: {st.session_state['lat_input']}, {st.session_state['lng_input']}")
elif st.session_state.get("geo_pending", False):
    st.info("Lokasiya icazəsi gözlənilir... (Brauzerdə Allow seç)")
else:
    st.caption("Məkan hələ təyin edilməyib")

# ---- FORM ----
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    magaza_adi = st.text_input("🏪 Mağaza Adı *")
    sahibkar = st.text_input("👤 Sahibkarın Adı")
    magaza_tipi = st.selectbox("🏗️ Mağaza Tipi", ["Banyo", "Banyo və Xırdavat", "Xırdavat"])

with col2:
    rayon = st.selectbox(
        "📍 Rayon",
        ["Lənkəran", "Masallı", "Astara", "Lerik", "Yardımlı", "Cəlilabad", "Biləsuvar", "Salyan", "Digər"],
    )
    telefon = st.text_input("📞 Əlaqə Nömrəsi")
    satici_var = st.radio("Satıcısı varmı?", ["Var", "Yox"], horizontal=True)

hecm_listi = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 10000, 20000]
hecm = st.selectbox("📦 Həcm (AZN/Mal)", hecm_listi)

st.write("📍 **Koordinatlar**")
c_lat, c_lng = st.columns(2)
with c_lat:
    st.text_input("Enlik (Lat)", key="lat_input")
with c_lng:
    st.text_input("Uzunluq (Lng)", key="lng_input")

# Kamera (Streamlit məcburi rear seçə bilmir)
uploaded_photo = st.camera_input("📸 Mağaza Şəkli (telefon arxa kameraya keçirsənsə daha yaxşıdır)")
qeyd = st.text_area("📝 Qeydlər")

# ---- SAVE ----
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi.strip():
        st.error("⚠️ Mağaza Adı mütləqdir!")
    else:
        # Auth clients
        try:
            gc, drive = get_clients()
            ws = ensure_worksheet(gc)
        except Exception as e:
            st.error(f"Google bağlantı xətası: {e}")
            st.stop()

        # şəkli Drive-a yüklə
        photo_link = ""
        if uploaded_photo is not None:
            try:
                img_bytes = uploaded_photo.getvalue()
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in magaza_adi.strip()])
                fn = f"{ts}_{safe_name}.jpg"
                photo_link = upload_image_to_drive(drive, img_bytes, fn)
            except Exception as e:
                st.warning(f"Şəkil Drive-a yüklənmədi: {e}")
                photo_link = ""

        # Row hazırlanır (səliqəli sxem)
        row = {
            "Tarix": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Mağaza": magaza_adi.strip(),
            "Rayon": rayon,
            "Tip": magaza_tipi,
            "Sahibkar": sahibkar.strip(),
            "Telefon": telefon.strip(),
            "Satıcı Var?": satici_var,
            "Həcm": hecm,
            "Latitude": st.session_state.get("lat_input", ""),
            "Longitude": st.session_state.get("lng_input", ""),
            "Şəkil Linki": photo_link,
            "Qeyd": qeyd.strip(),
        }

        # Sheets-ə yaz
        try:
            append_row(ws, row)
        except Exception as e:
            st.error(f"Sheets-ə yazılmadı: {e}")
            st.stop()

        st.success("✅ Məlumatlar Google Sheets-ə yazıldı və şəkil Drive-a yükləndi!")

# ---- ARXİV (Sheets-dən oxu) ----
st.markdown("---")
if st.checkbox("📊 Arxivə bax (Sheets-dən)"):
    try:
        gc, _ = get_clients()
        ws = ensure_worksheet(gc)
        values = ws.get_all_values()
        if len(values) <= 1:
            st.info("Hələ data yoxdur.")
        else:
            df = pd.DataFrame(values[1:], columns=values[0])
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Arxiv oxunmadı: {e}")