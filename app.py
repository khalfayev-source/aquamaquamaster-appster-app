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

# --- JAVASCRIPT GEOLOKASİYA (AYRI-AYRI) ---
def get_location_js():
    js_code = """
    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px dashed #4285F4; text-align: center;">
        <button id="geoBtn" onclick="getLocation()" style="padding: 12px 24px; background-color: #4285F4; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
            📍 MƏKANI TƏYİN ET
        </button>
        <p id="status" style="margin-top: 10px; font-size: 14px; font-family: sans-serif; color: #555;">Məkan hələ təyin edilməyib</p>
    </div>

    <script>
    function getLocation() {
      const status = document.getElementById('status');
      if (navigator.geolocation) {
        status.innerText = "Koordinatlar alınır...";
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            status.innerText = "Tapıldı: " + lat.toFixed(6) + ", " + lng.toFixed(6);
            
            // Streamlit-ə JSON formatında göndəririk
            window.parent.postMessage({
              type: 'streamlit:set_component_value',
              value: {lat: lat, lng: lng}
            }, '*');
          },
          (error) => {
            status.innerText = "Xəta: " + error.message;
          },
          { enableHighAccuracy: true }
        );
      } else { 
        status.innerText = "Brauzer dəstəkləmir.";
      }
    }
    </script>
    """
    return components.html(js_code, height=130)

# --- DATA YADDA SAXLA ---
def save_data(store_name, district, store_type, owner, phone, has_seller, volume, lat, lng, photo_file, note):
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
        "Həcm": [volume], "Enlik (Lat)": [lat], "Uzunluq (Lng)": [lng], 
        "Şəkil": [photo_path], "Qeyd": [note]
    }
    df_new = pd.DataFrame(new_row)
    if os.path.exists(EXCEL_FILE):
        df_old = pd.read_excel(EXCEL_FILE)
        pd.concat([df_old, df_new], ignore_index=True).to_excel(EXCEL_FILE, index=False)
    else:
        df_new.to_excel(EXCEL_FILE, index=False)
    return True

# --- APP ---
st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# 1. Məkan Düyməsi
loc_data = get_location_js()

lat_val = ""
lng_val = ""

if loc_data and isinstance(loc_data, dict):
    lat_val = loc_data.get('lat', "")
    lng_val = loc_data.get('lng', "")

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

    st.write("📍 **Koordinatlar**")
    col_lat, col_lng = st.columns(2)
    with col_lat:
        final_lat = st.text_input("Enlik (Lat)", value=str(lat_val))
    with col_lng:
        final_lng = st.text_input("Uzunluq (Lng)", value=str(lng_val))

    uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
    qeyd = st.text_area("📝 Qeydlər")

    if st.form_submit_button("💾 YADDA SAXLA"):
        if not magaza_adi:
            st.error("⚠️ Mağaza Adı mütləqdir!")
        else:
            save_data(magaza_adi, rayon, magaza_tipi, sahibkar, telefon, satici_var, hecm, final_lat, final_lng, uploaded_photo, qeyd)
            st.success("✅ Məlumatlar yadda saxlanıldı!")
            st.balloons()

# 3. ARXİV BÖLMƏSİ
st.markdown("---")
if st.checkbox("📊 Arxivlənmiş yazılara bax"):
    if os.path.exists(EXCEL_FILE):
        df_view = pd.read_excel(EXCEL_FILE)
        st.dataframe(df_view)
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("📥 Excel-i Yüklə", f, file_name="aquamaster_baza.xlsx")
    else:
        st.info("Hələ ki, baza boşdur.")