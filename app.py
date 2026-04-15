import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - Strict Mode", page_icon="🚗")

# თქვენი Google API გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.markdown("# 🚗 VIN AI Pro (Strict Mode)")
st.write("ვალიდაციის მაღალი დონე - მხოლოდ რეალური VIN კოდები")

def is_valid_vin(vin):
    # მკაცრი შემოწმება: 17 სიმბოლო, არანაირი I, O, Q
    if len(vin) != 17:
        return False
    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
        return False
    return True

def scan_vin_strict(image_bytes):
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
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        # ვასუფთავებთ ყველაფრისგან, გარდა ასოებისა და ციფრებისა
        potential_blocks = re.findall(r'[A-Z0-9]+', full_text.upper())
        
        valid_vins = []
        for block in potential_blocks:
            # თუ ბლოკი გრძელია, ვჭრით 17 სიმბოლოდ და ვამოწმებთ
            for i in range(len(block) - 16):
                sub_block = block[i:i+17]
                if is_valid_vin(sub_block):
                    valid_vins.append(sub_block)
        
        if valid_vins:
            # ვაბრუნებთ პირველს, რომელიც ფილტრში გაძვრა
            return valid_vins[0]
            
    return None

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("სკანირება"):
        with st.spinner("მიმდინარეობს მკაცრი ვალიდაცია..."):
            final_result = scan_vin_strict(uploaded_file.getvalue())
            
            if final_result:
                st.success("✅ ნაპოვნია ვალიდური VIN კოდი:")
                st.code(final_result, language='text')
            else:
                st.error("❌ ფოტოზე ვალიდური VIN კოდი არ არსებობს ან ვერ ამოიცნო.")
                st.info("შენიშვნა: პროგრამა მხოლოდ 17-ნიშნა კოდს იღებს (I, O, Q ასოების გარეშე).")
