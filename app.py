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

# --- 100% İŞLƏYƏN JAVASCRIPT GEOLOKASİYA ---
def get_location_js():
    js_code = """
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d1d1;">
        <p style="margin: 0 0 10px 0; font-family: sans-serif; font-size: 14px; color: #31333F;">📍 Məkanınızı müəyyənləşdirin:</p>
        <button id="geoBtn" onclick="getLocation()" style="width: 100%; padding: 10px; background-color: #FF4B4B; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
            📍 KOORDİNATI GÖTÜR
        </button>
        <p id="status" style="margin-top: 10px; font-size: 12px; color: #555;"></p>
    </div>

    <script>
    function getLocation() {
      const btn = document.getElementById('geoBtn');
      const status = document.getElementById('status');
      
      if (navigator.geolocation) {
        status.innerText = "Axtarılır...";
        navigator.geolocation.getCurrentPosition(showPosition, showError);
      } else { 
        status.innerText = "Brauzer geolokasiyanı dəstəkləmir.";
      }
    }

    function showPosition(position) {
      const coords = position.coords.latitude + "," + position.coords.longitude;
      document.getElementById('status').innerText = "Tapıldı: " + coords;
      
      // Streamlit-ə datanı göndərmək
      window.parent.postMessage({
        type: 'streamlit:set_component_value',
        value: coords
      }, '*');
    }

    function showError(error) {
      document.getElementById('status').innerText = "Xəta: " + error.message;
    }
    </script>
    """
    return components.html(js_code, height=120)

# --- DATA YADDA SAXLA ---
def save_data(store_name, district, store_type, owner, phone, has_seller, volume, coords, photo_file, note):
    photo_path = "Şəkil Yoxdur"
    if photo_file is not None:
        img = Image.open(photo_file)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fn = f"{ts}_{store_name.replace(' ', '_')}.jpg"
        save_path = os.path.join(IMAGE_FOLDER, fn)
        img.save(save_path)
        photo_path = save_path

    new_row = {
        "Tarix": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Mağaza": [store_name], "Rayon": [district], "Tip": [store_type],
        "Sahibkar": [owner], "Telefon": [phone], "Satıcı": [has_seller],
        "Həcm": [volume], "Koordinat": [coords], "Şəkil": [photo_path], "Qeyd": [note]
    }
    df_new = pd.DataFrame(new_row)
    if os.path.exists(EXCEL_FILE):
        pd.concat([pd.read_excel(EXCEL_FILE), df_new], ignore_index=True).to_excel(EXCEL_FILE, index=False)
    else:
        df_new.to_excel(EXCEL_FILE, index=False)
    return True

# --- APP ---
st.set_page_config(page_title="Aquamaster", page_icon="💧")
st.title("💧 Aquamaster")

# 1. JavaScript Koordinat Düyməsi (FORMDAN KƏNARDA OLMALIDIR)
coords_data = get_location_js()

# 2. Əsas Forma
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
        hecm_listi = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 10000, 20000]
        hecm = st.selectbox("📦 Həcm (AZN/Mal)", hecm_listi)

    # JS-dən gələn koordinatı bura bağlayırıq
    final_coords = st.text_input("📍 Təsdiqlənmiş Koordinat", value=coords_data if coords_data else "")

    uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
    qeyd = st.text_area("📝 Qeydlər")

    if st.form_submit_button("💾 YADDA SAXLA"):
        if not magaza_adi or not final_coords:
            st.error("⚠️ Mağaza Adı və Koordinat mütləqdir!")
        else:
            save_data(magaza_adi, rayon, magaza_tipi, sahibkar, telefon, satici_var, hecm, final_coords, uploaded_photo, qeyd)
            st.success("✅ Qeydə alındı!")
            st.balloons()