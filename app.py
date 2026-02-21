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

st.set_page_config(page_title="Aquamaster Cənub", page_icon="💧")
st.title("💧 Aquamaster")

# ---------- 1) URL query param-lardan lat/lng oxu ----------
# Streamlit (yeni) API: st.query_params
lat_from_url = st.query_params.get("lat", "")
lng_from_url = st.query_params.get("lng", "")

# Session state init
if "lat" not in st.session_state:
    st.session_state.lat = ""
if "lng" not in st.session_state:
    st.session_state.lng = ""

# URL-dən gəlibsə session-a yaz (widget-lardan ƏVVƏL)
if lat_from_url:
    st.session_state.lat = lat_from_url
if lng_from_url:
    st.session_state.lng = lng_from_url

# ---------- 2) JAVASCRIPT GEOLOKASİYA (query param ilə) ----------
def get_location_js():
    js_code = """
    <div style="background-color:#f9f9f9;padding:15px;border-radius:10px;border:1px dashed #4285F4;text-align:center;">
        <button onclick="getLocation()" style="padding:12px 24px;background-color:#4285F4;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:16px;">
            📍 MƏKANI TƏYİN ET
        </button>
        <p id="status" style="margin-top:10px;font-size:14px;font-family:sans-serif;color:#555;">Məkan hələ təyin edilməyib</p>
    </div>

    <script>
    function getLocation() {
      const status = document.getElementById('status');
      if (!navigator.geolocation) {
        status.innerText = "Brauzer dəstəkləmir.";
        return;
      }
      status.innerText = "Koordinatlar alınır...";
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude.toFixed(6);
          const lng = position.coords.longitude.toFixed(6);
          status.innerText = "Tapıldı: " + lat + ", " + lng;

          // ✅ Streamlit-ə value qaytara bilmirik, ona görə URL query param yazırıq
          const parentWin = window.parent;
          const url = new URL(parentWin.location.href);
          url.searchParams.set("lat", lat);
          url.searchParams.set("lng", lng);

          // yenidən yüklə (Streamlit python tərəf oxuyacaq)
          parentWin.location.href = url.toString();
        },
        (error) => {
          status.innerText = "Xəta: " + error.message;
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
      );
    }
    </script>
    """
    components.html(js_code, height=140)

get_location_js()

# ---------- 3) FORM ----------
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

st.write("📍 **Koordinatlar**")
col_lat, col_lng = st.columns(2)
with col_lat:
    final_lat = st.text_input("Enlik (Lat)", value=st.session_state.lat, key="lat_input")
with col_lng:
    final_lng = st.text_input("Uzunluq (Lng)", value=st.session_state.lng, key="lng_input")

uploaded_photo = st.camera_input("📸 Mağaza Şəkli")
qeyd = st.text_area("📝 Qeydlər")

# ---------- 4) SAVE ----------
if st.button("💾 YADDA SAXLA", use_container_width=True):
    if not magaza_adi:
        st.error("⚠️ Mağaza Adı mütləqdir!")
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
            "Həcm": [hecm],
            "Latitude": [final_lat],
            "Longitude": [final_lng],
            "Şəkil": [photo_path],
            "Qeyd": [qeyd]
        }
        df_new = pd.DataFrame(new_row)

        if os.path.exists(EXCEL_FILE):
            df_old = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new

        df_final.to_excel(EXCEL_FILE, index=False)
        st.success("✅ Məlumatlar yadda saxlanıldı!")

# ---------- 5) ARXİV ----------
st.markdown("---")
if st.checkbox("📊 Arxivə bax"):
    if os.path.exists(EXCEL_FILE):
        st.dataframe(pd.read_excel(EXCEL_FILE))
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("📥 Excel-i Yüklə", f, file_name="aquamaster_baza.xlsx")