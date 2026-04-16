import streamlit as st
import requests
import base64
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="Car VIN Searcher", layout="wide")

# Google Vision API გასაღები VIN-ის ამოსაცნობად
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
        text = res_json['responses'][0]['textAnnotations'][0]['description']
        # ეძებს 17 სიმბოლოიან VIN ფორმატს
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except:
        return None

# --- ინტერფეისი ---
st.title("🚗 Car VIN Searcher")

if st.session_state.step == 1:
    st.header("🔎 ნაბიჯი 1: VIN-ის ამოცნობა")
    st.write("ატვირთეთ ფოტო, სადაც ჩანს VIN კოდი.")
    
    file = st.file_uploader("აირჩიეთ ფაილი", type=['jpg', 'jpeg', 'png'])
    
    if file and st.button("ამოცნობა და ძიება 🚀"):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            vin_code = extract_vin(file.getvalue())
            if vin_code:
                st.session_state.vin = vin_code
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ ამოიცნო. სცადეთ სხვა ფოტო ან შეიყვანეთ ხელით.")
                
    manual_vin = st.text_input("ან შეიყვანეთ VIN ხელით:")
    if manual_vin and st.button("ხელით ძიება"):
        st.session_state.vin = manual_vin.upper()
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header(f"🔍 ძიება VIN-ით: {st.session_state.vin}")
    
    st.write("გამოიყენეთ ქვემოთ მოცემული ღილაკი ინფორმაციის მოსაძიებლად:")
    
    # მხოლოდ Google ძიების ფუნქცია
    google_url = f"https://www.google.com/search?q={st.session_state.vin}"
    st.link_button("🌐 მოძებნე Google-ში", google_url, use_container_width=True)
    
    st.divider()
    
    if st.button("🔄 სხვა კოდის შემოწმება"):
        st.session_state.step = 1
        st.session_state.vin = None
        st.rerun()
