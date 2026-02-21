import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from streamlit_js_eval import get_geolocation

# --- TƏNZİMLƏMƏLƏR ---
EXCEL_FILE = "aquamaster_data.xlsx"
IMAGE_FOLDER = "magaza_sekilleri"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- SƏHİFƏ ---
st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# --- SESSION STATE INIT ---
st.session_state.setdefault("lat", "")
st.session_state.setdefault("lng", "")

# --- GEOLOKASİYA BLOKU ---
st.markdown("### 📍 Məkan")
col_geo1, col_geo2 = st.columns([1, 2])
with col_geo1:
    geo_click = st.button("📍 MƏKANI TƏYİN ET", use_container_width=True)

loc = None
# get_geolocation() komponenti düymə basılandan sonra işləsin deyə:
# - düymə basılanda rerun olur
# - həmin rerunda komponent dəyəri qaytarır (icazə verilibsə)
if geo_click or st.session_state.get("geo_pending", False):
    st.session_state["geo_pending"] = True
    loc = get_geolocation()

# loc oxu və session-a yaz
if isinstance(loc, dict):
    coords = loc.get("coords") or {}
    lat = coords.get("latitude")
    lng = coords.get("longitude")
    if lat is not None and lng is not None:
        st.session_state.lat = f"{float(lat):.6f}"
        st.session_state.lng = f"{float(lng):.6f}"
        st.session_state["geo_pending"] = False

# status göstəricisi
if st.session_state.lat and st.session_state.lng:
    st.success(f"Tapıldı: {st.session_state.lat}, {st.session_state.lng}")
elif st.session_state.get("geo_pending", False):
    st.info("Lokasiya icazəsi gözlənilir... (Brauzerdə Allow seç)")
else:
    st.caption("Məkan hələ təyin edilməyib")

# --- FORM BLOKU ---
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    magaza_adi = st.text_input("🏪 Mağaza Adı *")
    sahibkar = st.text_input("👤 Sahibkarın Adı")
    magaza_tipi = st.selectbox("🏗️ Mağaza Tipi", ["Banyo", "Banyo və Xırdavat", "Xırdavat"])

with col2:
    rayon = st.selectbox("📍 Rayon", ["Lənkəran", "Masallı", "Astara", "Lerik", "Yardımlı", "Cəlilabad", "Biləsuvar", "Salyan", "Digər"])
    telefon = st.text_input("📞 Əlaqə Nömrəsi")
    satici_var = st.radio("Satıcısı varmı?", ["Var", "Yox"], horizontal=True)

hecm_listi = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 10000, 20000]
hecm = st.selectbox("📦 Həcm (AZN/Mal)", hecm_listi)

st.write("📍 **Koordinatlar**")
col_lat, col_lng = st.columns(2)
with col_lat:
    final_lat = st.text_input("Enlik (Lat)", value=st.session_state.lat, key="lat_input")
with col_lng:
    final_lng = st.text_input("Uzunluq (Lng)", value=st.session_state.lng, key="lng_input")

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

# --- YADDA SAXLA ---
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi:
        st.error("⚠️ Mağaza Adı mütləqdir!")
    else:
        photo_path = "Şəkil Yoxdur"
        if uploaded_photo is not None:
            img = Image.open(uploaded_photo)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join([c if c.isalnum() or c in "_-" else "_" for c in magaza_adi.strip()])
            fn = f"{ts}_{safe_name}.jpg"
            save_path = os.path.join(IMAGE_FOLDER, fn)
            img.save(save_path)
            photo_path = save_path

        new_row = {
            "Tarix": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Mağaza": [magaza_adi],
            "Rayon": [rayon],
            "Tip": [magaza_tipi],
            "Sahibkar": [sahibkar],
            "Telefon": [telefon],
            "Satıcı": [satici_var],
            "Həcm": [hecm],
            "Latitude": [final_lat],
            "Longitude": [final_lng],
            "Şəkil": [photo_path],
            "Qeyd": [qeyd]
        }
        df_new = pd.DataFrame(new_row)

        if os.path.exists(EXCEL_FILE):
            df_old = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new

        df_final.to_excel(EXCEL_FILE, index=False)
        st.success("✅ Məlumatlar yadda saxlanıldı!")

# --- ARXİV ---
st.markdown("---")
if st.checkbox("📊 Arxivə bax"):
    if os.path.exists(EXCEL_FILE):
        st.dataframe(pd.read_excel(EXCEL_FILE), use_container_width=True)
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("📥 Excel-i Yüklə", f, file_name="aquamaster_baza.xlsx")
    else:
        st.info("Hələ heç bir məlumat yoxdur.")