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

def save_data(store_name, district, store_type, owner, phone, has_seller, volume, lat, long, photo_file, note):
    photo_path = "Şəkil Yoxdur"
    if photo_file is not None:
        img = Image.open(photo_file)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        clean_name = store_name.replace(" ", "_").replace("/", "-")
        filename = f"{timestamp}_{clean_name}.jpg"
        save_path = os.path.join(IMAGE_FOLDER, filename)
        img.save(save_path)
        photo_path = save_path

    new_data = {
        "Tarix": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Mağaza Adı": [store_name],
        "Rayon": [district],
        "Mağaza Tipi": [store_type],
        "Sahibkar": [owner],
        "Telefon": [phone],
        "Satıcı Var?": [has_seller],
        "Həcm": [volume],
        "Latitude": [lat],
        "Longitude": [long],
        "Şəkil Yolu": [photo_path],
        "Qeyd": [note]
    }
    df_new = pd.DataFrame(new_data)
    if os.path.exists(EXCEL_FILE):
        df_old = pd.read_excel(EXCEL_FILE)
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = df_new
    df_final.to_excel(EXCEL_FILE, index=False)
    return True

st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# --- AVTOMATİK GEOLOKASİYA ---
loc = get_geolocation()

lat_val = ""
long_val = ""

# Xətanın qarşısını almaq üçün burada yoxlama edirik
if loc is not None:
    if 'coords' in loc:
        lat_val = str(loc['coords'].get('latitude', ""))
        long_val = str(loc['coords'].get('longitude', ""))
        if lat_val and long_val:
            st.success(f"📍 Məkan təyin edildi: {lat_val}, {long_val}")
else:
    st.info("🌐 Məkan təyin edilir... Zəhmət olmasa brauzerdə icazə verin.")

# --- ƏSAS FORMA ---
with st.form("main_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        magaza_adi = st.text_input("🏪 Mağaza Adı *")
    with col2:
        rayon = st.selectbox("📍 Rayon", ["Lənkəran", "Masallı", "Astara", "Lerik", "Yardımlı", "Cəlilabad", "Biləsuvar", "Salyan", "Digər"])

    magaza_tipi = st.selectbox("🏗️ Mağaza Tipi", ["Banyo", "Banyo və Xırdavat", "Xırdavat"])
    
    col3, col4 = st.columns(2)
    with col3:
        sahibkar = st.text_input("👤 Sahibkarın Adı")
    with col4:
        telefon = st.text_input("📞 Əlaqə Nömrəsi")

    col5, col6 = st.columns(2)
    with col5:
        satici_var = st.radio("Satıcısı varmı?", ["Var", "Yox"], horizontal=True)
    with col6:
        hecm_listi = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000]
        hecm = st.selectbox("📦 Həcm (AZN/Mal)", hecm_listi)

    st.write("🌍 **Koordinatlar**")
    lat = st.text_input("Latitude", value=lat_val)
    long = st.text_input("Longitude", value=long_val)

    uploaded_photo = st.camera_input("📸 Şəkil çək")
    qeyd = st.text_area("📝 Xüsusi Qeyd")

    submitted = st.form_submit_button("💾 YADDA SAXLA")
    if submitted:
        if not magaza_adi:
            st.error("⚠️ Mağaza Adı mütləqdir!")
        else:
            save_data(magaza_adi, rayon, magaza_tipi, sahibkar, telefon, satici_var, hecm, lat, long, uploaded_photo, qeyd)
            st.success("✅ Məlumatlar yadda saxlanıldı!")
            st.balloons()

# Admin üçün bazaya baxış
with st.expander("📊 Mövcud Bazaya Bax"):
    if os.path.exists(EXCEL_FILE):
        st.dataframe(pd.read_excel(EXCEL_FILE))