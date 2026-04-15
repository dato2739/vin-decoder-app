import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - Final Logic", page_icon="🚗")

# თქვენი Google API გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.markdown("# 🚗 VIN AI Pro (Strict Mode)")
st.write("ლოგიკა: 1. დიგიტალიზაცია | 2. მხოლოდ 17-ნიშნა ბლოკები | 3. VIN ვალიდაცია")

def is_valid_vin(vin):
    # მკაცრი შემოწმება: 17 სიმბოლო, არანაირი I, O, Q
    if len(vin) != 17:
        return False
    # რადგან O უკვე ჩავანაცვლეთ 0-ით, აქ ვამოწმებთ სტანდარტულ ფორმატს
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
        # 1. ვიღებთ მთლიან ტექსტს თავისი პრაბელებით
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        
        # გადაგვყავს ციფრულ ფორმატში: დიდ ასოებად და O-ს ვცვლით 0-ით
        processed_text = full_text.upper().replace('O', '0')
        
        # 2. ვყოფთ ტექსტს ბლოკებად პრაბელების და ახალი ხაზების მიხედვით
        # ვიყენებთ split()-ს, რომელიც ინახავს ორიგინალ დაყოფას
        potential_blocks = processed_text.split()
        
        for block in potential_blocks:
            # ვასუფთავებთ ბლოკს ზედმეტი სიმბოლოებისგან (მაგ. წერტილი, მძიმე ბოლოში)
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            
            # 3. განვიხილავთ მხოლოდ იმ ჩანაწერს, რომელიც არის ზუსტად 17 სიმბოლო
            if len(clean_block) == 17:
                # 4. თუ არის 17 სიმბოლო, გადავამოწმოთ VIN სტანდარტზე
                if is_valid_vin(clean_block):
                    return clean_block
            else:
                # თუ 17-ზე ნაკლებია ან მეტია - იგნორირება
                continue
                
    return None

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("სკანირება"):
        with st.spinner("მიმდინარეობს მკაცრი ლოგიკური ფილტრაცია..."):
            final_result = scan_vin_strict(uploaded_file.getvalue())
            
            if final_result:
                st.success("✅ ნაპოვნია ვალიდური 17-ნიშნა VIN კოდი:")
                st.code(final_result, language='text')
            else:
                st.error("❌ ვალიდური 17-ნიშნა VIN კოდი ვერ მოიძებნა.")
                st.info("სისტემამ მოახდინა სხვა მონაცემების იგნორირება (წონა, თარიღი), რადგან ისინი არ იყვნენ 17 სიმბოლო.")
