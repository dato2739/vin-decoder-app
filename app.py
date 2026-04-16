import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - Decoder", page_icon="🚗", layout="centered")

# თქვენი Google API გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def get_vin_details(vin):
    """NHTSA API-დან მონაცემების გამოთხოვა"""
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()['Results'][0]
            return {
                "მარკა": data.get("Make"),
                "მოდელი": data.get("Model"),
                "წელი": data.get("ModelYear"),
                "ძრავა": f"{data.get('DisplacementL')}L {data.get('EngineConfiguration')}{data.get('EngineCylinders')}",
                "ქვეყანა": data.get("PlantCountry")
            }
    except:
        return None
    return None

def scan_vin_strict(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {
        "requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]
    }
    response = requests.post(url, json=payload)
    result = response.json()
    
    if 'responses' in result and result['responses'][0]:
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        processed_text = full_text.upper().replace('O', '0')
        potential_blocks = processed_text.split()
        
        for block in potential_blocks:
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            if len(clean_block) == 17 and is_valid_vin(clean_block):
                return clean_block
    return None

# ინტერფეისი
st.markdown("<h1 style='text-align: center;'>🚗 VIN AI Pro</h1>", unsafe_allow_html=True)
st.write("---")

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("სკანირება და გაშიფვრა", use_container_width=True):
        with st.spinner("მიმდინარეობს ანალიზი..."):
            vin = scan_vin_strict(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ კოდი ამოცნობილია: {vin}")
                
                # დეკოდირება
                details = get_vin_details(vin)
                if details and details['მარკა']:
                    st.write("### 📋 ავტომობილის მონაცემები:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("მარკა", details['მარკა'])
                        st.metric("მოდელი", details['მოდელი'])
                    with col2:
                        st.metric("წელი", details['წელი'])
                        st.metric("ქვეყანა", details['ქვეყანა'])
                    st.info(f"⚙️ ძრავის მონაცემები: {details['ძრავა']}")
                else:
                    st.warning("კოდი ამოცნობილია, მაგრამ დეტალური ინფორმაცია ბაზაში ვერ მოიძებნა.")
            else:
                st.error("❌ ვალიდური 17-ნიშნა VIN კოდი ვერ მოიძებნა.")
