import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN AI Pro - v1.6", page_icon="🚗", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def scan_vin_strict(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        if 'responses' in result and result['responses'][0].get('textAnnotations'):
            full_text = result['responses'][0]['textAnnotations'][0]['description']
            for block in full_text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17: return clean
    except: pass
    return None

def get_bid_cars_images(vin):
    search_url = f"https://bid.cars/en/search/results?q={vin}"
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={search_url}&javascript=true"
    image_links = []
    try:
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for img in soup.find_all('img', src=True):
                src = img['src']
                if "b-cdn.net" in src and "photos" in src:
                    full_img = src.replace("-thumbnail", "")
                    if full_img not in image_links: image_links.append(full_img)
    except: pass
    return image_links

# --- ლოგიკა ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro")
    file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])
    if file:
        st.image(file, width=350)
        if st.button("ანალიზის დაწყება", use_container_width=True):
            vin = scan_vin_strict(file.getvalue())
            if vin:
                st.session_state['active_vin'] = vin
                with st.spinner("ვიძიებ ფოტოებს..."):
                    st.session_state['auction_images'] = get_bid_cars_images(vin)
                st.session_state['page'] = 'analysis'
                st.rerun()
            else:
                st.error("❌ VIN ვერ მოიძებნა")

elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    if st.button("⬅️ უკან"): 
        st.session_state['page'] = 'home'
        st.rerun()
    
    st.header(f"🔎 VIN: {vin}")
    imgs = st.session_state.get('auction_images', [])
    if imgs:
        st.success(f"ნაპოვნია {len(imgs)} ფოტო")
        cols = st.columns(3)
        for i, url in enumerate(imgs):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("სურათები ვერ მოიძებნა bid.cars-ზე.")
    
    st.divider()
    st.link_button("ნახე bid.cars-ზე", f"https://bid.cars/en/search/results?q={vin}")
