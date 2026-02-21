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

# --- GOOGLE MAPS-DƏKİ KİMİ JS GEOLOKASİYA ---
def get_location_js():
    js_code = """
    <script>
    function getLocation() {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
      } else { 
        window.parent.postMessage({type: 'streamlit:set_component_value', value: 'Geolokasiya dəstəklənmir'}, '*');
      }
    }

    function showPosition(position) {
      const coords = position.coords.latitude + "," + position.coords.longitude;
      window.parent.postMessage({type: 'streamlit:set_component_value', value: coords}, '*');
    }

    function showError(error) {
      window.parent.postMessage({type: 'streamlit:set_component_value', value: 'Xəta: ' + error.message}, '*');
    }
    
    // Səhifə yüklənən kimi işə düşsün
    getLocation();
    </script>
    <button onclick="getLocation()" style="padding: 10px 20px; background-color: #008CBA; color: white; border: none; border-radius: 5px; cursor: pointer;">📍 Koordinatı Yenilə</button>
    """
    return components.html(js_code, height=60)

# --- DATA YADDA SAXLA ---
def save_data(store_name, district, store_type, owner, phone, has_seller, volume, coords, photo_file, note):
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
        "Koordinatlar": [coords],
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

# --- APP DİZAYN ---
st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

st.subheader("🌍 Məkan Təyini")
# JS vasitəsilə məkənı alırıq
coords_from_js = get_location_js()

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

    st.write("📍 **Koordinatlar**")
    # Brauzerdən gələn datanı bura yazırıq
    final_coords = st.text_input("Enlik və Uzunluq (Avtomatik dolur)", value=coords_from_js if coords_from_js else "")

    uploaded_photo = st.camera_input("📸 Şəkil çək")
    qeyd = st.text_area("📝 Xüsusi Qeyd")

    submitted = st.form_submit_button("💾 YADDA SAXLA")
    if submitted:
        if not magaza_adi:
            st.error("⚠️ Mağaza Adı mütləqdir!")
        else:
            save_data(magaza_adi, rayon, magaza_tipi, sahibkar, telefon, satici_var, hecm, final_coords, uploaded_photo, qeyd)
            st.success("✅ Məlumatlar uğurla qeydə alındı!")
            st.balloons()