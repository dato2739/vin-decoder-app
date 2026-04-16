import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - Smart Hub", page_icon="🚗", layout="centered")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

# ფუნქცია, რომელიც ამოწმებს NHTSA-ს ბაზას
def get_vin_details(vin):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            res = response.json()['Results'][0]
            # თუ მარკა ცარიელია, ნიშნავს რომ ბაზაში ეს კონკრეტული VIN არ დევს
            if not res.get("Make"): return None
            return res
    except: return None
    return None

# ფუნქცია, რომელიც ამოწმებს არის თუ არა მანქანა აუქციონზე (სიმულაცია სწრაფი პასუხისთვის)
def check_info_availability(vin):
    availability = {
        "bidfax": True,  # BidFax-ს თითქმის ყოველთვის აქვს ამერიკულებზე
        "nhtsa": False,
        "carfax": True   # Carfax-ს ყოველთვის აქვს ჩანაწერი, თუ მანქანა არსებობს
    }
    # NHTSA-ს რეალური შემოწმება
    details = get_vin_details(vin)
    if details:
        availability["nhtsa"] = True
    
    return availability, details

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

st.markdown("<h1 style='text-align: center;'>🚗 VIN AI Pro - Smart Hub</h1>", unsafe_allow_html=True)
st.write("---")

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("ანალიზი და იდენტიფიკაცია", use_container_width=True):
        with st.spinner("სისტემა ამოწმებს ბაზებს..."):
            vin = scan_vin_strict(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ ამოცნობილია: {vin}")
                avail, details = check_info_availability(vin)
                
                if details:
                    st.write(f"### 📋 {details.get('ModelYear')} {details.get('Make')} {details.get('Model')}")
                
                st.write("---")
                st.write("🔍 **ხელმისაწვდომი ინფორმაცია:**")
                
                col1, col2 = st.columns(2)
                
                # BidFax ღილაკი - ყოველთვის აქტიურია ამერიკულებისთვის
                with col1:
                    st.link_button("🖼️ აუქციონის ფოტოები (BidFax)", f"https://bidfax.info/search/f/vin/{vin}/", use_container_width=True)
                
                # NHTSA ღილაკი - მხოლოდ თუ API-მ დააბრუნა პასუხი
                with col2:
                    if avail["nhtsa"]:
                        st.link_button("🛡️ უსაფრთხოება (NHTSA)", f"https://www.nhtsa.gov/recalls?vin={vin}", use_container_width=True)
                    else:
                        st.button("🛡️ უსაფრთხოება (მონაცემები არ არის)", disabled=True, use_container_width=True)

                col3, col4 = st.columns(2)
                with col3:
                    st.link_button("📜 ისტორია (PLC.ua)", f"https://plc.ua/ca/vin-check/?vin={vin}", use_container_width=True)
                
                with col4:
                    # Carfax - ყოველთვის ჩანს როგორც ოფიციალური წყარო
                    st.link_button("📊 Carfax რეპორტი", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
                
                # თუ კოდი ევროპულია (არ იწყება 1, 2, 3, 4, 5-ით)
                if not vin.startswith(('1','2','3','4','5')):
                    st.info("💡 ეს კოდი ევროპული ჩანს. რეკომენდებულია AutoDNA-ზე შემოწმება.")
                    st.link_button("🇪🇺 ევროპული ბაზა (AutoDNA)", f"https://www.autodna.com/vin/{vin}", use_container_width=True)
            else:
                st.error("❌ ვალიდური VIN ვერ მოიძებნა. სცადეთ სხვა ფოტო.")
