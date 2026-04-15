import streamlit as st
import requests
import base64
import re
from PIL import Image
import io

# გვერდის სათაური
st.set_page_config(page_title="Professional VIN AI Pro", page_icon="🚗")

# --- თქვენი Google API გასაღები ---
GOOGLE_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

st.markdown("# 🚗 Professional VIN AI Pro")
st.write("Google Cloud Vision - მაქსიმალური სიზუსტის ამოცნობა")

def scan_vin_google(image_bytes):
    # სურათის მომზადება Google Cloud Vision-ისთვის
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"
    
    # ლოგიკა: "ამოიცანი ტექსტი"
    payload = {
        "requests": [{
            "image": {"content": encoded_image},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    
    # მოთხოვნა Google Cloud Vision API-ზე
    response = requests.post(url, json=payload)
    data = response.json()
    
    if 'responses' in data and data['responses'][0]:
        # ვიღებთ მთლიან ამოცნობილ ტექსტს ფოტოდან (სტიკერზე რაც წერია)
        full_text = data['responses'][0]['textAnnotations'][0]['description']
        
        # ვასუფთავებთ ტექსტს: ვაშორებთ "სფეისებს" და სხვა არაალფანუმერულ სიმბოლოებს
        clean_text = re.sub(r'\s+', '', full_text).upper()
        
        # --- ჭკვიანი ფილტრი ---
        # "რეგულარული გამოსახულება" (Regex) 17-ნიშნა VIN-ის მოსაძებნად.
        # ის ეძებს კომბინაციას, რომელიც მხოლოდ ასოებისგან (A-Z) და ციფრებისგან (0-9) შედგება და არის ზუსტად 17 სიმბოლო.
        vin_pattern = re.compile(r'[A-HJ-NPR-Z0-9]{17}')
        
        # ვეძებთ მთლიან გასუფთავებულ ტექსტში პირველ 17-ნიშნა კომბინაციას
        match = vin_pattern.search(clean_text)
        
        if match:
            # თუ იპოვა, ვაბრუნებთ მხოლოდ მას
            return match.group(0)
        else:
            # თუ ზუსტი მატჩი არაა, ვცდილობთ ამოვიღოთ ნებისმიერი 17-ნიშნა ალფანუმერული კომბინაცია
            # (თუ მაგალითად Google-მა VIN-ში ასოები ციფრებად აღიქვა)
            secondary_match = re.search(r'[A-Z0-9]{17}', clean_text)
            return secondary_match.group(0) if secondary_match else "ვერ მოიძებნა"
            
    return "შეცდომა სკანირებისას"

# სურათის ატვირთვის ინტერფეისი
uploaded_file = st.file_uploader("ატვირთეთ ფოტო, რომელიც შეიცავს VIN კოდს", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # სურათის ჩვენება გვერდზე
    st.image(uploaded_file, use_container_width=True)
    
    if st.button("სკანირება"):
        with st.spinner('Google AI აანალიზებს ფოტოს...'):
            # ვუკავშირდებით Google AI-ს და ვიღებთ მხოლოდ 17-ნიშნა VIN კოდს
            final_vin = scan_vin_google(uploaded_file.getvalue())
            
            st.success("ამოცნობილია:")
            st.subheader(final_vin)
