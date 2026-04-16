import streamlit as st
import requests
import base64
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="ვინ კოდით ძებნა", layout="wide")

# Google Vision API გასაღები
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None

def extract_vin(image_bytes):
    """ამოიცნობს VIN კოდს ფოტოდან Google Vision-ის გამოყენებით"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": encoded},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        res_json = response.json()
        if 'responses' in res_json and res_json['responses'][0]:
            text = res_json['responses'][0]['textAnnotations'][0]['description']
            # ეძებს 17 სიმბოლოიან VIN ფორმატს
            match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
            return match.group(0) if match else None
        return None
    except:
        return None

# --- ინტერფეისი ---
st.title("ვინ კოდით ძებნა")

if st.session_state.step == 1:
    st.subheader("ატვირთეთ ვინ კოდის სურათი")
    
    file = st.file_uploader("აირჩიეთ ფაილი (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
    
    if file and st.button("ამოცნობა და ძიება 🚀"):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            vin_code = extract_vin(file.getvalue())
            if vin_code:
                st.session_state.vin = vin_code
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ ამოიცნო. სცადეთ სხვა ფოტო.")
                
    st.divider()
    manual_vin = st.text_input("ან შეიყვანეთ VIN ხელით:")
    if manual_vin and st.button("ძიება"):
        st.session_state.vin = manual_vin.upper().strip()
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header(f"ნაპოვნია VIN: {st.session_state.vin}")
    
    # მხოლოდ Google-ის ძიების ბმული
    google_url = f"https://www.google.com/search?q={st.session_state.vin}"
    
    st.info("დააჭირეთ ღილაკს ინფორმაციის სანახავად:")
    st.link_button("🌐 მოძებნე Google-ში", google_url, use_container_width=True)
    
    st.divider()
    
    if st.button("🔄 სხვა მანქანის შემოწმება"):
        st.session_state.step = 1
        st.session_state.vin = None
        st.rerun()
