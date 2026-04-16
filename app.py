import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="AI Car Analyzer", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def process_images(image_list):
    """ყველა ატვირთული ფოტოს დამუშავება ერთიანად"""
    combined_results = {"text_data": {}, "visual_notes": []}
    
    for img in image_list:
        encoded = base64.b64encode(img.getvalue()).decode('utf-8')
        url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
        payload = {
            "requests": [{
                "image": {"content": encoded},
                "features": [{"type": "TEXT_DETECTION"}, {"type": "LABEL_DETECTION"}]
            }]
        }
        
        try:
            res = requests.post(url, json=payload).json()
            annotations = res['responses'][0]
            
            # ტექსტის ამოკრეფა (ფასი, გარბენი, VIN)
            if 'textAnnotations' in annotations:
                text = annotations['textAnnotations'][0]['description']
                
                # VIN ძებნა
                vin = re.search(r'[A-Z0-9]{17}', text)
                if vin: combined_results["text_data"]["VIN"] = vin.group(0)
                
                # ფასის ძებნა
                price = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
                if price: combined_results["text_data"]["ბოლო ფასი"] = price.group(0)
                
                # გარბენის ძებნა
                mileage = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:mi|miles|миль)', text, re.I)
                if mileage: combined_results["text_data"]["გარბენი"] = f"{mileage.group(1)} mi"

        except:
            continue
            
    return combined_results

st.title("🚗 კომპლექსური AI ანალიზი")
st.write("ატვირთეთ აუქციონის 6-მდე სქრინშოტი (მონაცემები + ფოტოები)")

# Multi-upload ფუნქცია
uploaded_files = st.file_uploader("ამოირჩიეთ სქრინშოტები", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    # გალერეის ჩვენება
    st.subheader("🖼️ ატვირთული ფაილები")
    cols = st.columns(min(len(uploaded_files), 6))
    for idx, file in enumerate(uploaded_files):
        cols[idx].image(file, use_container_width=True)
    
    if len(uploaded_files) > 6:
        st.warning("გთხოვთ, შემოიფარგლოთ 6 ფოტოთი საუკეთესო შედეგისთვის.")
    
    if st.button("🚀 დაიწყე სრული ანალიზი", use_container_width=True):
        with st.spinner("AI აანალიზებს სქრინშოტებს..."):
            results = process_images(uploaded_files)
            
            st.divider()
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("📊 ამოკრებილი მონაცემები")
                if results["text_data"]:
                    for k, v in results["text_data"].items():
                        st.write(f"**{k}:** {v}")
                else:
                    st.info("ტექსტური მონაცემები ვერ მოიძებნა. დარწმუნდით, რომ ატვირთეთ აუქციონის დეტალების სქრინშოტი.")
            
            with col_b:
                st.subheader("🤖 AI შეფასება")
                # აქ შეგვიძლია დავამატოთ ლოგიკა, რომელიც აფასებს მონაცემებს
                if "გარბენი" in results["text_data"]:
                    st.success("✅ მონაცემები მიღებულია. AI გირჩევთ ისტორიის გადამოწმებას.")
