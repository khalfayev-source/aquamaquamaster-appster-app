import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components
import json

EXCEL_FILE = "aquamaster_data.xlsx"
IMAGE_FOLDER = "magaza_sekilleri"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# ---- SESSION STATE ----
if "lat" not in st.session_state:
    st.session_state.lat = ""
if "lng" not in st.session_state:
    st.session_state.lng = ""

# ---- GEO JS COMPONENT ----
def get_location_js():
    js_code = """
    <button onclick="getLocation()" 
        style="padding:12px 24px;background:#4285F4;color:white;border:none;border-radius:8px;font-weight:bold;">
        📍 MƏKANI TƏYİN ET
    </button>
    <p id="status">Məkan təyin edilməyib</p>

    <script>
    function getLocation(){
        const status = document.getElementById("status");
        if (!navigator.geolocation){
            status.innerText = "Brauzer dəstəkləmir";
            return;
        }
        status.innerText = "Alınır...";
        navigator.geolocation.getCurrentPosition(
            (pos)=>{
                const lat = pos.coords.latitude.toFixed(6);
                const lng = pos.coords.longitude.toFixed(6);
                status.innerText = "Tapıldı: " + lat + ", " + lng;

                const data = {lat: lat, lng: lng};
                window.parent.postMessage(
                    {type: "streamlit:setComponentValue", value: data},
                    "*"
                );
            },
            (err)=>{ status.innerText = err.message; },
            {enableHighAccuracy:true}
        );
    }
    </script>
    """
    return components.html(js_code, height=150)

st.title("💧 Aquamaster")

# ---- GEO COMPONENT ----
loc = get_location_js()

# ---- DATA PYTHON TƏRƏFƏ KEÇİR ----
if loc:
    st.session_state.lat = loc.get("lat", "")
    st.session_state.lng = loc.get("lng", "")

# ---- FORM ----
st.markdown("---")

magaza_adi = st.text_input("🏪 Mağaza Adı *")
rayon = st.text_input("Rayon")

st.write("📍 Koordinatlar")

col1, col2 = st.columns(2)
with col1:
    final_lat = st.text_input("Enlik (Lat)", value=st.session_state.lat)
with col2:
    final_lng = st.text_input("Uzunluq (Lng)", value=st.session_state.lng)

qeyd = st.text_area("Qeyd")

if st.button("💾 YADDA SAXLA"):
    if not magaza_adi:
        st.error("Mağaza adı boş ola bilməz")
    else:
        new_row = {
            "Tarix": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "Mağaza": [magaza_adi],
            "Rayon": [rayon],
            "Latitude": [final_lat],
            "Longitude": [final_lng],
            "Qeyd": [qeyd]
        }

        df_new = pd.DataFrame(new_row)

        if os.path.exists(EXCEL_FILE):
            df_old = pd.read_excel(EXCEL_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new

        df_final.to_excel(EXCEL_FILE, index=False)

        st.success("Yadda saxlanıldı ✅")