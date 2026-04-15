import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro", page_icon="🚗")

# შენი ახალი გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.markdown("# 🚗 VIN AI Pro")
st.write("Google Cloud AI - პროფესიონალური სკანერი")

def scan_vin(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    
    payload = {
        "requests": [{
            "image": {"content": encoded_image},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if 'responses' in result and result['responses'][0]:
        # Google პოულობს მთლიან ტექსტს ფოტოზე
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        # ვასუფთავებთ ზედმეტი სიმბოლოებისგან
        clean_text = re.sub(r'[^A-Z0-9]', '', full_text.upper())
        # ვეძებთ ზუსტად 17 სიმბოლოს
        match = re.search(r'[A-Z0-9]{17}', clean_text)
        return match.group(0) if match else clean_text[:17]
    return None

uploaded_file = st.file_uploader("ატვირთეთ VIN კოდის ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("კოდის ამოცნობა"):
        with st.spinner("Google AI აანალიზებს..."):
            vin = scan_vin(uploaded_file.getvalue())
            if vin:
                st.success("✅ ამოცნობილია:")
                st.code(vin, language='text')
            else:
                st.error("ვერ მოხერხდა ამოცნობა. სცადეთ სხვა ფოტო.")
