import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro", page_icon="🚗")

# თქვენი გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.markdown("# 🚗 VIN AI Pro")
st.write("სისტემა ფოკუსირებულია მხოლოდ VIN კოდის პოვნაზე")

def extract_vin_smart(image_bytes):
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
        # ვიღებთ მთლიან ტექსტს ფოტოდან
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        
        # ვასუფთავებთ ტექსტს სფეისებისგან და ვხდით ყველაფერს დიდ ასოებად
        cleaned_text = re.sub(r'\s+', '', full_text).upper()
        
        # ლოგიკა: ვეძებთ ზუსტად 17 სიმბოლოს, რომელიც შეიცავს ასოებს და ციფრებს
        # VIN არ შეიცავს ასოებს: I, O, Q
        vin_matches = re.findall(r'[A-HJ-NPR-Z0-9]{17}', cleaned_text)
        
        if vin_matches:
            # თუ რამდენიმე იპოვა, ავიღოთ ის, რომელიც ყველაზე მეტად ჰგავს VIN-ს
            return vin_matches[0]
        
        # თუ ზემოთ მოცემული მკაცრი ფილტრით ვერ იპოვა, ვცადოთ უფრო ზოგადი 17 სიმბოლო
        fallback_match = re.search(r'[A-Z0-9]{17}', cleaned_text)
        return fallback_match.group(0) if fallback_match else "VIN ვერ მოიძებნა"
            
    return "კავშირის შეცდომა"

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("სკანირება"):
        with st.spinner("მიმდინარეობს ფილტრაცია..."):
            vin = extract_vin_smart(uploaded_file.getvalue())
            if vin != "VIN ვერ მოიძებნა":
                st.success("✅ ნაპოვნია VIN კოდი:")
                st.subheader(vin)
            else:
                st.error("სტიკერზე VIN კოდი ვერ გამოიყო. სცადეთ უფრო ახლოდან გადაღება.")
