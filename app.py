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

# --- JAVASCRIPT KOORDİNAT DÜYMƏSİ ---
def get_location_button():
    # Bu kod birbaşa brauzerin daxili GPS-ini çağırır
    js_code = """
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 2px solid #4285F4; text-align: center;">
        <button id="getLocBtn" onclick="getLocation()" style="width: 100%; padding: 15px; background-color: #4285F4; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
            📍 MƏKANI TƏYİN ET (DÜYMƏYƏ BASIN)
        </button>
        <p id="out" style="margin-top: 10px; font-family: sans-serif; font-size: 14px; color: #333;">Koordinat gözlənilir...</p>
    </div>

    <script>
    function getLocation() {
      const output = document.getElementById('out');
      if (navigator.geolocation) {
        output.innerText = "Axtarılır...";
        navigator.geolocation.getCurrentPosition(showPosition, showError);
      } else { 
        output.innerText = "Brauzer geolokasiyanı dəstəkləmir.";
      }
    }

    function showPosition(position) {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      document.getElementById('out').innerText = "Tapıldı: " + lat + ", " + lng;
      
      // Streamlit-ə datanı göndərmək
      window.parent.postMessage({
        type: 'streamlit:set_component_value',
        value: lat + "," + lng
      }, '*');
    }

    function showError(error) {
      document.getElementById('out').innerText = "Xəta: " + error.message;
    }
    </script>
    """
    return components.html(js_code, height=150)

# --- APP ---
st.set_page_config(page_title="Aquamaster", page_icon="💧")
st.title("💧 Aquamaster")

# 1. JAVASCRIPT DÜYMƏSİ (BURADADIR)
st.subheader("🌍 Məkan Təyini")
coords_raw = get_location_button()

# 2. DATA PARÇALAMA
lat_final = ""
lng_final = ""
if coords_raw:
    try:
        lat_final, lng_final = coords_raw.split(",")
        st.success(f"✅ Koordinat mənimsənildi: {lat_final}, {lng_final}")
    except:
        pass

# 3. FORMA
st.markdown("---")
# Formun içindəkiləri rahat doldurmaq üçün xanaları sadə saxlayırıq
magaza_adi = st.text_input("🏪 Mağaza Adı *")
rayon = st.selectbox("📍 Rayon", ["Lənkəran", "Masallı", "Astara", "Lerik", "Yardımlı", "Cəlilabad", "Biləsuvar", "Salyan", "Digər"])
magaza_tipi = st.selectbox("🏗️ Mağaza Tipi", ["Banyo", "Banyo və Xırdavat", "Xırdavat"])

col1, col2 = st.columns(2)
with col1:
    sahibkar = st.text_input("👤 Sahibkarın Adı")
    satici_var = st.radio("Satıcısı varmı?", ["Var", "Yox"], horizontal=True)
with col2:
    telefon = st.text_input("📞 Əlaqə Nömrəsi")
    hecm = st.selectbox("📦 Həcm (AZN/Mal)", [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 10000, 20000])

st.write("📍 **Koordinat Xanaları (Avtomatik dolacaq)**")
final_lat = st.text_input("Enlik (Lat)", value=lat_final)
final_lng = st.text_input("Uzunluq (Lng)", value=lng_final)

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi or not final_lat:
        st.error("⚠️ Mağaza Adı və Koordinatlar mütləqdir! Düyməni sıxıb koordinatı götürün.")
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
            pd.concat([pd.read_excel(EXCEL_FILE), df_new], ignore_index=True).to_excel(EXCEL_FILE, index=False)
        else:
            df_new.to_excel(EXCEL_FILE, index=False)
        st.success("✅ Məlumatlar uğurla qeydə alındı!")
        st.balloons()