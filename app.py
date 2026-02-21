import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components

# Google Kitabxanaları
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- TƏNZİMLƏMƏLƏR ---
SERVICE_ACCOUNT_FILE = "key.json" # GitHub-a yüklədiyin faylın adı
SPREADSHEET_ID = "1PO8vl6lVCio9lHgFrZFQ9Sgz6XRbVOWYyh8FMZzaM9E"
DRIVE_FOLDER_ID = "1SgXAWg6xxyq4L_UmFiaQeo8yE5bCZVXu"

# --- GOOGLE BAĞLANTISI FUNKSİYASI ---
def get_g_services():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gc, drive_service

# --- DRIVE-A ŞƏKİL YÜKLƏMƏ FUNKSİYASI ---
def upload_image_to_drive(drive_service, photo_bytes, filename):
    file_metadata = {'name': filename, 'parents': [DRIVE_FOLDER_ID]}
    media = MediaIoBaseUpload(io.BytesIO(photo_bytes), mimetype='image/jpeg')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    # Şəkli hamı görə bilsin deyə icazə veririk
    drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'viewer'}).execute()
    return file.get('webViewLink')

# --- JAVASCRIPT KOORDİNAT DÜYMƏSİ ---
def get_location_js():
    js_code = """
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #4285F4; text-align: center;">
        <button id="geoBtn" onclick="getLocation()" style="width: 100%; padding: 12px; background-color: #4285F4; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
            📍 MƏKANI TƏYİN ET
        </button>
        <p id="status" style="margin-top: 10px; font-size: 14px; font-family: sans-serif; color: #333;">Məkan hələ təyin edilməyib</p>
    </div>
    <script>
    function getLocation() {
      const status = document.getElementById('status');
      if (navigator.geolocation) {
        status.innerText = "Axtarılır...";
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const coords = pos.coords.latitude + "|" + pos.coords.longitude;
            status.innerText = "✅ Tapıldı və Köçürüldü!";
            window.parent.postMessage({type: 'streamlit:set_component_value', value: coords}, '*');
          },
          (err) => { status.innerText = "Xəta: " + err.message; },
          { enableHighAccuracy: true }
        );
      }
    }
    </script>
    """
    return components.html(js_code, height=130)

# --- APP BAŞLIĞI ---
st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# 1. Məkan Düyməsi
coords_raw = get_location_js()

# 2. Giriş Xanaları
st.markdown("---")
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

# Koordinatları parçalayırıq
st.session_state.setdefault('lat', "")
st.session_state.setdefault('lng', "")
if coords_raw and "|" in coords_raw:
    st.session_state.lat, st.session_state.lng = coords_raw.split("|")

st.write("📍 **Koordinatlar (Avtomatik dolur)**")
col_lat, col_lng = st.columns(2)
final_lat = col_lat.text_input("Enlik (Lat)", value=st.session_state.lat)
final_lng = col_lng.text_input("Uzunluq (Lng)", value=st.session_state.lng)

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

# --- YADDA SAXLA (GOOGLE SHEETS-Ə) ---
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi or not final_lat:
        st.error("⚠️ Mağaza Adı və Koordinatlar mütləqdir!")
    else:
        try:
            with st.spinner("Məlumatlar Google Sheets-ə göndərilir..."):
                gc, drive_service = get_g_services()
                
                # 1. Şəkli Drive-a yüklə
                photo_link = "Şəkil Yoxdur"
                if uploaded_photo:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fn = f"{ts}_{magaza_adi}.jpg"
                    photo_link = upload_image_to_drive(drive_service, uploaded_photo.getvalue(), fn)
                
                # 2. Sətiri hazırla
                new_row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    magaza_adi, rayon, magaza_tipi, sahibkar, telefon, 
                    satici_var, hecm, final_lat, final_lng, photo_link, qeyd
                ]
                
                # 3. Sheets-ə yaz
                sh = gc.open_by_key(SPREADSHEET_ID)
                sh.sheet1.append_row(new_row)
                
                st.success("✅ Məlumatlar Google Sheets-ə uğurla yazıldı!")
                st.balloons()
        except Exception as e:
            st.error(f"Xəta: {e}")

# --- ARXİV ---
st.markdown("---")
if st.checkbox("📊 Canlı Bazaya Bax"):
    try:
        gc, _ = get_g_services()
        sh = gc.open_by_key(SPREADSHEET_ID)
        df_view = pd.DataFrame(sh.sheet1.get_all_records())
        st.dataframe(df_view, use_container_width=True)
    except:
        st.info("Baza hələ boşdur və ya qoşulma xətası var.")