import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from streamlit_js_eval import streamlit_js_eval

# --- TƏNZİMLƏMƏLƏR ---
EXCEL_FILE = "aquamaster_data.xlsx"
IMAGE_FOLDER = "magaza_sekilleri"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- APP BAŞLIĞI ---
st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# --- GEOLOKASİYA (SESSION STATE İLƏ) ---
st.subheader("🌍 Məkan Təyini")

# JavaScript vasitəsilə koordinatı götürürük
loc = streamlit_js_eval(
    js_expressions="done => { navigator.geolocation.getCurrentPosition( (pos) => { done(pos.coords.latitude + ',' + pos.coords.longitude) } ) }", 
    key='get_loc'
)

# Sessiya yaddaşını yoxlayırıq
if loc:
    st.session_state['lat_long'] = str(loc)
    st.success(f"📍 Koordinatlar alındı: {st.session_state['lat_long']}")
else:
    if 'lat_long' not in st.session_state:
        st.session_state['lat_long'] = ""
    st.info("🌐 Məkan təyin edilir... Brauzerdə icazə verin.")

# --- ƏSAS FORMA ---
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

# Koordinat Xanaları - Session State-dən gələn məlumatı bura yazırıq
st.write("📍 **Koordinatlar**")
col_lat, col_lng = st.columns(2)

# Koordinatı parçalayırıq (vergüllə ayrılıb)
lat_input = ""
lng_input = ""
if st.session_state['lat_long']:
    lat_input, lng_input = st.session_state['lat_long'].split(",")

with col_lat:
    final_lat = st.text_input("Enlik (Lat)", value=lat_input)
with col_lng:
    final_lng = st.text_input("Uzunluq (Lng)", value=lng_input)

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

# Yadda Saxla Düyməsi
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi:
        st.error("⚠️ Mağaza Adı mütləqdir!")
    elif not final_lat or not final_lng:
        st.error("⚠️ Koordinatlar hələ alınmayıb! Zəhmət olmasa bir az gözləyin və ya səhifəni yeniləyin.")
    else:
        photo_path = "Şəkil Yoxdur"
        if uploaded_photo is not None:
            img = Image.open(uploaded_photo)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fn = f"{ts}_{magaza_adi.replace(' ', '_')}.jpg"
            save_path = os.path.join(IMAGE_FOLDER, fn)
            img.save(save_path)
            photo_path = save_path

        new_row = {
            "Tarix": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Mağaza": [magaza_adi], "Rayon": [rayon], "Tip": [magaza_tipi],
            "Sahibkar": [sahibkar], "Telefon": [telefon], "Satıcı": [satici_var],
            "Həcm": [hecm], "Latitude": [final_lat], "Longitude": [final_lng], 
            "Şəkil": [photo_path], "Qeyd": [qeyd]
        }
        df_new = pd.DataFrame(new_row)
        
        if os.path.exists(EXCEL_FILE):
            df_old = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new
            
        df_final.to_excel(EXCEL_FILE, index=False)
        st.success("✅ Məlumatlar uğurla yadda saxlanıldı!")
        st.balloons()

# Arxiv
st.markdown("---")
if st.checkbox("📊 Arxivə bax"):
    if os.path.exists(EXCEL_FILE):
        st.dataframe(pd.read_excel(EXCEL_FILE))