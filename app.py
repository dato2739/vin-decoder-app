import streamlit as st
import requests
import base64
import re

# კონფიგურაცია
st.set_page_config(page_title="VIN AI Investigator", layout="centered")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# Session State-ის ინიციალიზაცია, რომ აპმა ნაბიჯები დაიმახსოვროს
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'vin' not in st.session_state:
    st.session_state.vin = None

def scan_text(image_bytes):
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload).json()
        return res['responses'][0]['textAnnotations'][0]['description']
    except: return ""

# --- ეტაპი 1: VIN-ის აღება ---
if st.session_state.step == 1:
    st.title("Step 1: 📸 VIN სკანირება")
    mode = st.radio("აირჩიეთ წყარო:", ["კამერა", "გალერეა"], horizontal=True)
    
    source = st.camera_input("გადაუღეთ VIN-ს") if mode == "კამერა" else st.file_uploader("ატვირთეთ VIN")
    
    if source and st.button("შემდეგი ➡️"):
        text = scan_text(source.getvalue())
        vin_match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        if vin_match:
            st.session_state.vin = vin_match.group(0)
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("VIN კოდი ვერ ამოიცნო. სცადეთ თავიდან.")

# --- ეტაპი 2: ციფრული VIN და ლინკები ---
elif st.session_state.step == 2:
    st.title("Step 2: 🔗 ძებნა და ბმულები")
    st.success(f"ამოცნობილი VIN: **{st.session_state.vin}**")
    
    col1, col2, col3 = st.columns(3)
    col1.link_button("Google Search", f"https://www.google.com/search?q={st.session_state.vin}+auction")
    col2.link_button("BidFax Search", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    col3.link_button("Bid.cars", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
    
    st.info("მოძებნეთ ინფორმაცია ამ ლინკებზე, გადაუღეთ სქრინშოტები და დაბრუნდით აქ.")
    if st.button("გადავიდეთ ატვირთვაზე ➡️"):
        st.session_state.step = 3
        st.rerun()

# --- ეტაპი 3: სქრინშოტების ატვირთვა ---
elif st.session_state.step == 3:
    st.title("Step 3: 📤 სქრინშოტების მიწოდება")
    st.write(f"VIN: {st.session_state.vin}")
    
    screenshots = st.file_uploader("ატვირთეთ აუქციონის სურათები და ინფო (max 6)", 
                                  type=['jpg', 'png', 'jpeg'], 
                                  accept_multiple_files=True)
    
    if screenshots and st.button("ანალიზის დაწყება 🚀"):
        st.session_state.screenshots = screenshots
        st.session_state.step = 4
        st.rerun()

# --- ეტაპი 4: გაფართოებული ანალიზი ---
elif st.session_state.step == 4:
    st.title("Step 4: 🧠 AI ექსპერტიზა")
    
    with st.spinner("AI ამუშავებს მონაცემებს..."):
        all_text = ""
        for img in st.session_state.screenshots:
            all_text += scan_text(img.getvalue()) + " "
        
        # მარტივი ლოგიკა მონაცემების გამოსატანად
        price = re.search(r'\$(\d{1,3}(?:,\d{3})*)', all_text)
        mileage = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:mi|miles)', all_text, re.I)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 მონაცემები")
            st.write(f"**ფასი:** {price.group(0) if price else 'ვერ მოიძებნა'}")
            st.write(f"**გარბენი:** {mileage.group(0) if mileage else 'ვერ მოიძებნა'}")
        
        with col2:
            st.subheader("📝 AI დასკვნა")
            if price and mileage:
                st.write("ანალიზი: მონაცემები წარმატებით იქნა ამოკითხული სქრინშოტებიდან.")
            else:
                st.warning("ზოგიერთი მონაცემი სქრინშოტზე ბუნდოვანია.")

    if st.button("თავიდან დაწყება 🔄"):
        st.session_state.step = 1
        st.session_state.vin = None
        st.rerun()
