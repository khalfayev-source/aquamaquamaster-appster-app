import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from streamlit_js_eval import get_geolocation

# --- TƏNZİMLƏMƏLƏR ---
EXCEL_FILE = "aquamaster_data.xlsx"
IMAGE_FOLDER = "magaza_sekilleri"

# Excel-də istədiyimiz SƏLİQƏLİ sütun sxemi (ardıcıllıq)
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
    "Şəkil Yolu",
    "Qeyd",
]

# Köhnə fayllardan gələn sinonim sütun adları (birləşdirmək üçün)
SYNONYMS = {
    "Mağaza": ["Mağaza", "Mağaza Adı", "Magaza", "Magaza_adi"],
    "Tip": ["Tip", "Mağaza Tipi", "Magaza Tipi"],
    "Satıcı Var?": ["Satıcı Var?", "Satıcı", "Satici", "Satici varmi?"],
    "Şəkil Yolu": ["Şəkil Yolu", "Şəkil", "Sekil", "Image", "Photo"],
    "Latitude": ["Latitude", "Enlik (Lat)", "Lat", "lat"],
    "Longitude": ["Longitude", "Uzunluq (Lng)", "Lng", "lon", "lng"],
    "Tarix": ["Tarix", "Timestamp", "Date", "Tarix/Saat"],
    "Rayon": ["Rayon", "Region"],
    "Sahibkar": ["Sahibkar", "Sahibkarın Adı", "Owner"],
    "Telefon": ["Telefon", "Əlaqə Nömrəsi", "Phone"],
    "Həcm": ["Həcm", "Hecm", "Həcm (AZN/Mal)"],
    "Qeyd": ["Qeyd", "Qeydlər", "Notes"],
}

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# --- SESSION STATE INIT ---
st.session_state.setdefault("lat_input", "")
st.session_state.setdefault("lng_input", "")
st.session_state.setdefault("geo_pending", False)

# ---------- Helpers ----------
def first_nonempty(series_list):
    """Return first non-empty value across multiple series for each row."""
    if not series_list:
        return pd.Series(dtype="object")
    out = series_list[0].copy()
    for s in series_list[1:]:
        out = out.mask(out.isna() | (out.astype(str).str.strip() == ""), s)
    return out

def normalize_existing_excel(path: str) -> pd.DataFrame:
    """Read existing Excel and normalize to CANON_COLS (merge synonyms, drop extras, order cols)."""
    try:
        df = pd.read_excel(path)
    except Exception:
        return pd.DataFrame(columns=CANON_COLS)

    # Build canonical columns by merging synonyms
    canon = {}
    for canon_name, candidates in SYNONYMS.items():
        present = [c for c in candidates if c in df.columns]
        if present:
            canon[canon_name] = first_nonempty([df[c] for c in present])
        else:
            canon[canon_name] = ""

    out = pd.DataFrame(canon)

    # Ensure all canonical columns exist and order them
    for c in CANON_COLS:
        if c not in out.columns:
            out[c] = ""

    out = out[CANON_COLS]
    return out

def append_and_save(new_row_df: pd.DataFrame, path: str):
    """Normalize old file, append new row, enforce schema & order, then save."""
    if os.path.exists(path):
        df_old = normalize_existing_excel(path)
        df_final = pd.concat([df_old, new_row_df], ignore_index=True)
    else:
        df_final = new_row_df.copy()

    # Enforce exact columns & order, drop anything else
    for c in CANON_COLS:
        if c not in df_final.columns:
            df_final[c] = ""
    df_final = df_final[CANON_COLS]

    df_final.to_excel(path, index=False)

# ---------- GEO ----------
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

if st.session_state.get("lat_input") and st.session_state.get("lng_input"):
    st.success(f"Tapıldı: {st.session_state['lat_input']}, {st.session_state['lng_input']}")
elif st.session_state.get("geo_pending", False):
    st.info("Lokasiya icazəsi gözlənilir... (Brauzerdə Allow seç)")
else:
    st.caption("Məkan hələ təyin edilməyib")

# ---------- FORM ----------
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
col_lat, col_lng = st.columns(2)
with col_lat:
    st.text_input("Enlik (Lat)", key="lat_input")
with col_lng:
    st.text_input("Uzunluq (Lng)", key="lng_input")

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

# ---------- SAVE ----------
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi.strip():
        st.error("⚠️ Mağaza Adı mütləqdir!")
    else:
        # şəkil saxla
        photo_path = ""
        if uploaded_photo is not None:
            img = Image.open(uploaded_photo)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in magaza_adi.strip()])
            fn = f"{ts}_{safe_name}.jpg"
            save_path = os.path.join(IMAGE_FOLDER, fn)
            img.save(save_path)
            photo_path = save_path

        lat_to_save = st.session_state.get("lat_input", "")
        lng_to_save = st.session_state.get("lng_input", "")

        # yalnız CANON_COLS ilə yeni sətir yaradırıq (artıq map link yoxdur)
        new_row = {
            "Tarix": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Mağaza": magaza_adi.strip(),
            "Rayon": rayon,
            "Tip": magaza_tipi,
            "Sahibkar": sahibkar.strip(),
            "Telefon": telefon.strip(),
            "Satıcı Var?": satici_var,
            "Həcm": hecm,
            "Latitude": lat_to_save,
            "Longitude": lng_to_save,
            "Şəkil Yolu": photo_path or "Şəkil Yoxdur",
            "Qeyd": qeyd.strip(),
        }
        df_new = pd.DataFrame([new_row], columns=CANON_COLS)

        append_and_save(df_new, EXCEL_FILE)
        st.success("✅ Məlumatlar səliqəli formatda yadda saxlanıldı!")

# ---------- ARXİV ----------
st.markdown("---")
if st.checkbox("📊 Arxivə bax"):
    if os.path.exists(EXCEL_FILE):
        df_show = normalize_existing_excel(EXCEL_FILE)
        st.dataframe(df_show, use_container_width=True)
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("📥 Excel-i Yüklə", f, file_name="aquamaster_baza.xlsx")
    else:
        st.info("Hələ heç bir məlumat yoxdur.")