import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro", page_icon="🚗")

# თქვენი გასაღები (სურათიდან)
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.title("🚗 VIN AI Pro")

def get_vin_from_google(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    
    payload = {
        "requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]
    }
    
    response = requests.post(url, json=payload)
    res_data = response.json()
    
    if 'responses' in res_data and res_data['responses'][0]:
        full_text = res_data['responses'][0]['textAnnotations'][0]['description']
        
        # ვასუფთავებთ ტექსტს სფეისებისგან
        clean_text = re.sub(r'\s+', '', full_text).upper()
        
        # ვეძებთ ზუსტად 17 სიმბოლოს, რომელიც VIN-ის წესებს იცავს (I, O, Q-ს გარეშე)
        vin_pattern = re.compile(r'[A-HJ-NPR-Z0-9]{17}')
        match = vin_pattern.search(clean_text)
        
        if match:
            return match.group(0)
    return None

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    st.image(uploaded_file)
    if st.button("კოდის ამოცნობა"):
        result = get_vin_from_google(uploaded_file.getvalue())
        if result:
            st.success(f"ნაპოვნია VIN: {result}")
        else:
            st.error("ვალიდური VIN კოდი ვერ მოიძებნა. სცადეთ სხვა კუთხით.")
