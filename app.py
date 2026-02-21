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

# --- APP DİZAYN ---
st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# --- GEOLOKASİYA (ƏN STABİL ÜSUL) ---
st.subheader("🌍 Məkan Təyini")

# Brauzerdən koordinatları soruşuruq
loc = streamlit_js_eval(js_expressions="done => { navigator.geolocation.getCurrentPosition( (pos) => { done(pos.coords.latitude + ',' + pos.coords.longitude) } ) }", key='get_loc')

final_coords = ""
if loc:
    final_coords = str(loc)
    st.success(f"📍 Koordinatlar alındı: {final_coords}")
else:
    st.info("🌐 Məkan təyin edilir... Zəhmət olmasa brauzerdə icazə verin. Əgər düymə görünmürsə, səhifəni yeniləyin.")

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

    st.write("📍 **Təsdiqlənmiş Koordinatlar**")
    # Brauzerdən gələn koordinatı bura yazırıq
    coords_input = st.text_input("Enlik və Uzunluq", value=final_coords)

    uploaded_photo = st.camera_input("📸 Şəkil çək")
    qeyd = st.text_area("📝 Xüsusi Qeyd")

    submitted = st.form_submit_button("💾 YADDA SAXLA")
    
    if submitted:
        if not magaza_adi:
            st.error("⚠️ Mağaza Adı mütləqdir!")
        else:
            # Data yadda saxla funksiyası (sadəlik üçün birbaşa burda yazıram)
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
                "Mağaza": [magaza_adi],
                "Rayon": [rayon],
                "Tip": [magaza_tipi],
                "Sahibkar": [sahibkar],
                "Telefon": [telefon],
                "Satıcı": [satici_var],
                "Həcm": [hecm],
                "Koordinat": [coords_input],
                "Şəkil": [photo_path],
                "Qeyd": [qeyd]
            }
            df_new = pd.DataFrame(new_row)
            if os.path.exists(EXCEL_FILE):
                df_old = pd.read_excel(EXCEL_FILE)
                pd.concat([df_old, df_new], ignore_index=True).to_excel(EXCEL_FILE, index=False)
            else:
                df_new.to_excel(EXCEL_FILE, index=False)
                
            st.success("✅ Məlumatlar uğurla qeydə alındı!")
            st.balloons()