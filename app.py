import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - Stable", page_icon="🚗")

# თქვენი Google API გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.title("🚗 VIN AI Pro")
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
        
        # ვასუფთავებთ ტექსტს: ვცვლით O-ს 0-ით და დიდ ასოებად
        processed_text = full_text.upper().replace('O', '0')
        
        # ვყოფთ ტექსტს ბლოკებად პრაბელების მიხედვით
        potential_blocks = processed_text.split()
        
        for block in potential_blocks:
            # ვტოვებთ მხოლოდ ასოებსა და ციფრებს
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            
            # განვიხილავთ მხოლოდ ზუსტად 17 სიმბოლოს
            if len(clean_block) == 17:
                if is_valid_vin(clean_block):
                    return clean_block
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
                
                # სწრაფი ლინკები მომხმარებლისთვის
                st.write("🔍 **შეამოწმეთ ბაზებში:**")
                google_url = f"https://www.google.com/search?q={final_result}+auction+copart+iaai"
                st.link_button("🌐 მოძებნე Google-ში", google_url)
                st.link_button("🖼️ BidFax (აუქციონები)", f"https://bidfax.info/index.php?do=search&subaction=search&story={final_result}")
            else:
                st.error("❌ ვალიდური 17-ნიშნა VIN კოდი ვერ მოიძებნა.")
