import io
from datetime import datetime

import streamlit as st
import pandas as pd

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from streamlit_js_eval import get_geolocation


# =========================
# CONFIG
# =========================
SHEET_ID = "1PO8vl6lVCio9lHgFrZFQ9Sgz6XRbVOWYyh8FMZzaM9E"
DRIVE_FOLDER_ID = "1SgXAWg6xxyq4L_UmFiaQeo8yE5bCZVXu"
WORKSHEET_NAME = "Data"

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

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# =========================
# DEBUG (TEMP)
# =========================
def debug_secrets_private_key():
    st.markdown("### 🧪 DEBUG (Secrets private_key)")
    if "gcp_service_account" not in st.secrets:
        st.error("DEBUG: st.secrets içində [gcp_service_account] tapılmadı.")
        return

    info = dict(st.secrets["gcp_service_account"])
    pk = info.get("private_key", "")

    st.write("DEBUG private_key length:", len(pk))
    st.write("DEBUG contains BEGIN:", "BEGIN PRIVATE KEY" in pk)
    st.write("DEBUG contains END:", "END PRIVATE KEY" in pk)
    st.write("DEBUG contains literal \\\\n:", "\\n" in pk)
    st.write("DEBUG newline count:", pk.count("\n"))
    st.write("DEBUG head:", pk[:30].replace("\n", "\\n"))
    st.write("DEBUG tail:", pk[-30:].replace("\n", "\\n"))

    st.caption("Qeyd: Bu debug private key-i göstərmir, sadəcə format yoxlayır.")


# =========================
# GOOGLE AUTH (SECRETS ONLY)
# =========================
def _load_sa_info_from_secrets() -> dict:
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Streamlit Secrets-də [gcp_service_account] tapılmadı.")

    info = dict(st.secrets["gcp_service_account"])

    # Əgər kimsə tək-sətir formatı istifadə edibsə, \\n ola bilər — o halda düzəldirik.
    pk = info.get("private_key", "")
    if "\\n" in pk:
        info["private_key"] = pk.replace("\\n", "\n")

    return info


@st.cache_resource
def get_clients():
    info = _load_sa_info_from_secrets()
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    gc = gspread.authorize(creds)
    drive = build("drive", "v3", credentials=creds)
    return gc, drive, info.get("client_email", "unknown")


def ensure_worksheet(gc):
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows=2000, cols=len(CANON_COLS))

    header = ws.row_values(1)
    if header != CANON_COLS:
        ws.update("A1", [CANON_COLS])

    return ws


def append_row(ws, row_dict: dict):
    row = [row_dict.get(c, "") for c in CANON_COLS]
    ws.append_row(row, value_input_option="USER_ENTERED")


def upload_image_to_drive(drive, image_bytes: bytes, filename: str) -> str:
    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype="image/jpeg", resumable=False)
    file_metadata = {"name": filename, "parents": [DRIVE_FOLDER_ID]}

    created = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = created["id"]

    # Linklə baxış açıq olsun
    drive.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"


# =========================
# UI
# =========================
st.set_page_config(page_title="Aquamaster Cənub (Prod)", page_icon="💧")
st.title("💧 Aquamaster Cənub (Prod)")

# DEBUG BLOKU BURADA İŞLƏYİR
debug_secrets_private_key()

# ---- Auth check ----
try:
    gc, drive, sa_email = get_clients()
    st.caption(f"Google auth: OK ✅ ({sa_email})")
except Exception as e:
    st.error(f"Google auth xətası: {e}")
    st.stop()

# ---- session init ----
st.session_state.setdefault("lat_input", "")
st.session_state.setdefault("lng_input", "")
st.session_state.setdefault("geo_pending", False)

# ---- GEO ----
st.markdown("### 📍 Məkan")
geo_click = st.button("📍 MƏKANI TƏYİN ET", use_container_width=True)

loc = None
if geo_click or st.session_state.get("geo_pending", False):
    st.session_state["geo_pending"] = True
    loc = get_geolocation()

if isinstance(loc, dict):
    coords = loc.get("coords") or {}
    lat = coords.get("latitude", loc.get("latitude"))
    lng = coords.get("longitude", loc.get("longitude"))
    if lat is not None and lng is not None:
        st.session_state["lat_input"] = f"{float(lat):.6f}"
        st.session_state["lng_input"] = f"{float(lng):.6f}"
        st.session_state["geo_pending"] = False

if st.session_state["lat_input"] and st.session_state["lng_input"]:
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

uploaded_photo = st.camera_input("📸 Mağaza Şəkli (telefon arxa kameraya əl ilə keçə bilər)")
qeyd = st.text_area("📝 Qeydlər")

# ---- SAVE ----
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi.strip():
        st.error("⚠️ Mağaza Adı mütləqdir!")
        st.stop()

    try:
        ws = ensure_worksheet(gc)
    except Exception as e:
        st.error(f"Sheet açılmadı: {e}")
        st.stop()

    photo_link = ""
    if uploaded_photo is not None:
        try:
            img_bytes = uploaded_photo.getvalue()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in magaza_adi.strip()])
            filename = f"{ts}_{safe_name}.jpg"
            photo_link = upload_image_to_drive(drive, img_bytes, filename)
        except Exception as e:
            st.warning(f"Şəkil Drive-a yüklənmədi: {e}")
            photo_link = ""

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

    try:
        append_row(ws, row)
        st.success("✅ Məlumatlar Sheets-ə yazıldı, şəkil Drive-a yükləndi!")
    except Exception as e:
        st.error(f"Sheets-ə yazılmadı: {e}")
        st.stop()

# ---- ARCHIVE ----
st.markdown("---")
if st.checkbox("📊 Arxivə bax (Sheets-dən)"):
    try:
        ws = ensure_worksheet(gc)
        values = ws.get_all_values()
        if len(values) <= 1:
            st.info("Hələ data yoxdur.")
        else:
            df = pd.DataFrame(values[1:], columns=values[0])
            for c in CANON_COLS:
                if c not in df.columns:
                    df[c] = ""
            df = df[CANON_COLS]
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Arxiv oxunmadı: {e}")