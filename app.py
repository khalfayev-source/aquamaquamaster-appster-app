import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components

# --- TƏNZİMLƏMƏLƏR ---
EXCEL_FILE = "aquamaster_data.xlsx"
IMAGE_FOLDER = "magaza_sekilleri"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# --- JAVASCRIPT KOORDİNAT SİSTEMİ ---
def get_location_js():
    js_code = """
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 2px solid #4285F4; text-align: center; font-family: sans-serif;">
        <button id="getLocBtn" onclick="getLocation()" style="width: 100%; padding: 15px; background-color: #4285F4; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
            📍 MƏKANI TƏYİN ET
        </button>
        <p id="out" style="margin-top: 10px; font-size: 14px; color: #333; font-weight: bold;">Məkan gözlənilir...</p>
    </div>

    <script>
    function getLocation() {
      const output = document.getElementById('out');
      if (navigator.geolocation) {
        output.innerText = "Axtarılır...";
        navigator.geolocation.getCurrentPosition(showPosition, showError, {enableHighAccuracy: true});
      } else { 
        output.innerText = "Brauzer dəstəkləmir.";
      }
    }

    function showPosition(position) {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      document.getElementById('out').innerText = "✅ Tapıldı və Köçürüldü!";
      
      // Streamlit-ə datanı JSON kimi göndərmək
      window.parent.postMessage({
        type: 'streamlit:set_component_value',
        value: lat + "|" + lng
      }, '*');
    }

    function showError(error) {
      document.getElementById('out').innerText = "Xəta: " + error.message;
    }
    </script>
    """
    return components.html(js_code, height=160)

# --- APP ---
st.set_page_config(page_title="Aquamaster", page_icon="💧")
st.title("💧 Aquamaster")

# 1. Məkan Düyməsi
coords_raw = get_location_js()

# Koordinatları sessiya yaddaşında saxlayaq
if 'lat' not in st.session_state: st.session_state.lat = ""
if 'lng' not in st.session_state: st.session_state.lng = ""

if coords_raw and "|" in coords_raw:
    l_lat, l_lng = coords_raw.split("|")
    st.session_state.lat = l_lat
    st.session_state.lng = l_lng

# 2. GİRİŞ XANALARI
st.markdown("### 🏪 Mağaza Məlumatları")
magaza_adi = st.text_input("Mağaza Adı *")
rayon = st.selectbox("Rayon", ["Lənkəran", "Masallı", "Astara", "Lerik", "Yardımlı", "Cəlilabad", "Biləsuvar", "Salyan", "Digər"])
magaza_tipi = st.selectbox("Mağaza Tipi", ["Banyo", "Banyo və Xırdavat", "Xırdavat"])

col1, col2 = st.columns(2)
with col1:
    sahibkar = st.text_input("Sahibkarın Adı")
    satici_var = st.radio("Satıcısı varmı?", ["Var", "Yox"], horizontal=True)
with col2:
    telefon = st.text_input("Əlaqə Nömrəsi")
    hecm = st.selectbox("Həcm (AZN/Mal)", [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 10000, 20000])

st.markdown("---")
st.write("📍 **Koordinatlar**")
col_lat, col_lng = st.columns(2)
# Session state-dən gələn dəyərlər bura düşür
final_lat = col_lat.text_input("Enlik (Lat)", value=st.session_state.lat)
final_lng = col_lng.text_input("Uzunluq (Lng)", value=st.session_state.lng)

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

# 3. YADDA SAXLA
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi or not final_lat:
        st.error("⚠️ Mağaza Adı və Koordinatlar mütləqdir!")
    else:
        # DATA YADDA SAXLA
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
            pd.concat([df_old, df_new], ignore_index=True).to_excel(EXCEL_FILE, index=False)
        else:
            df_new.to_excel(EXCEL_FILE, index=False)
        
        st.success("✅ Məlumatlar uğurla qeydə alındı!")
        st.balloons()

# 4. ARXİV
with st.expander("📊 Arxivə bax"):
    if os.path.exists(EXCEL_FILE):
        st.dataframe(pd.read_excel(EXCEL_FILE))