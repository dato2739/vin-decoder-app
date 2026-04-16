import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - All-in-One", page_icon="🚗", layout="centered")

# თქვენი Google API გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def is_valid_vin(vin):
    if len(vin) != 17:
        return False
    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
        return False
    return True

def get_vin_details(vin):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['Results'][0]
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

# ინტერფეისი - გასწორებული TypeError
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
                st.code(vin, language='text')
                
                # ავტომატური გაშიფვრა
                data = get_vin_details(vin)
                if data and data.get("Make"):
                    st.write("### 📋 ავტომობილის მონაცემები:")
                    c1, c2 = st.columns(2)
                    c1.metric("მარკა", data.get("Make"))
                    c1.metric("მოდელი", data.get("Model"))
                    c2.metric("წელი", data.get("ModelYear"))
                    c2.metric("ქვეყანა", data.get("PlantCountry"))
                
                # --- ახალი ეტაპის ღილაკები ---
                st.write("---")
                st.write("🔍 **ისტორიის და ფოტოების შემოწმება:**")
                col_link1, col_link2 = st.columns(2)
                
                with col_link1:
                    st.link_button("BidFax (აუქციონის ფოტოები)", f"https://bidfax.info/search/f/vin/{vin}/")
                    st.link_button("PLC (ისტორია)", f"https://plc.ua/ca/vin-check/?vin={vin}")
                
                with col_link2:
                    st.link_button("NHTSA (უსაფრთხოება)", f"https://www.nhtsa.gov/recalls?vin={vin}")
                    st.link_button("Carfax (ოფიციალური რეპორტი)", f"https://www.carfax.com/vin/{vin}")
            else:
                st.error("❌ ვალიდური 17-ნიშნა VIN კოდი ვერ მოიძებნა.")
