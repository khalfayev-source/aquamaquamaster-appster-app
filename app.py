import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# --- TƏNZİMLƏMƏLƏR ---
EXCEL_FILE = "aquamaster_data.xlsx"
IMAGE_FOLDER = "magaza_sekilleri"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def save_data(store_name, district, store_type, owner, phone, has_seller, volume, map_link, photo_file, note):
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
        "Google Maps Linki": [map_link], # Koordinat əvəzinə Link
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

# --- FORMA ---
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

    # --- GEOLOKASİYA (GOOGLE MAPS ÜSULU) ---
    st.markdown("---")
    st.subheader("🌍 Məkan Təyini")
    
    st.write("1. Aşağıdakı düyməyə basaraq Google Maps-i açın.")
    st.write("2. Olduğunuz yeri seçib 'Share' (Paylaş) düyməsini sıxın və linki kopyalayın.")
    st.write("3. Linki aşağıdakı xanaya yapışdırın.")
    
    # Google Maps düyməsi (istifadəçini xəritəyə yönləndirir)
    maps_url = "https://www.google.com/maps"
    st.markdown(f'<a href="{maps_url}" target="_blank" style="text-decoration: none; padding: 10px 20px; background-color: #4285F4; color: white; border-radius: 5px;">📍 Google Maps-i Aç</a>', unsafe_input_context=True)
    
    map_link = st.text_input("Google Maps Linkini bura yapışdırın", placeholder="https://maps.app.goo.gl/...")

    st.markdown("---")
    uploaded_photo = st.camera_input("📸 Şəkil çək")
    qeyd = st.text_area("📝 Xüsusi Qeyd")

    submitted = st.form_submit_button("💾 YADDA SAXLA")
    if submitted:
        if not magaza_adi:
            st.error("⚠️ Mağaza Adı mütləqdir!")
        elif not map_link:
            st.warning("⚠️ Zəhmət olmasa Google Maps linkini əlavə edin.")
        else:
            save_data(magaza_adi, rayon, magaza_tipi, sahibkar, telefon, satici_var, hecm, map_link, uploaded_photo, qeyd)
            st.success("✅ Məlumatlar yadda saxlanıldı!")
            st.balloons()

# Arxiv (Excel yükləmə imkanı ilə)
with st.expander("📊 Arxivə Bax"):
    if os.path.exists(EXCEL_FILE):
        df_view = pd.read_excel(EXCEL_FILE)
        st.dataframe(df_view)
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("📥 Excel-i Yüklə", f, file_name="aquamaster_cenub.xlsx")