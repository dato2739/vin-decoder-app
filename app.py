import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - Smart Hub", page_icon="🚗", layout="centered")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def get_vin_details(vin):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            res = response.json()['Results'][0]
            if not res.get("Make"): return None
            return res
    except: return None
    return None

def scan_vin_strict(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
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
st.title("🚗 VIN AI Pro - Smart Hub")
st.write("---")

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("ანალიზი და იდენტიფიკაცია", use_container_width=True):
        with st.spinner("სისტემა ამოწმებს ბაზებს..."):
            vin = scan_vin_strict(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ ამოცნობილია: {vin}")
                details = get_vin_details(vin)
                
                if details:
                    st.subheader(f"📋 {details.get('ModelYear')} {details.get('Make')} {details.get('Model')}")
                
                st.write("---")
                st.write("🔍 **ხელმისაწვდომი ინფორმაცია:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # BidFax პირდაპირი ძებნა
                    bidfax_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
                    st.link_button("🖼️ აუქციონის ფოტოები (BidFax)", bidfax_url, use_container_width=True)
                
                with col2:
                    # Google Images ყველაზე საიმედოა ფოტოებისთვის
                    google_images_url = f"https://www.google.com/search?tbm=isch&q={vin}+auction+copart+iaai"
                    st.link_button("🌐 ფოტოები Google-ში", google_images_url, use_container_width=True)

                col3, col4 = st.columns(2)
