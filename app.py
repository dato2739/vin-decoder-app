import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN AI Pro - v1.7", page_icon="🚗", layout="wide")

# კონსტანტები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def get_vin_details(vin):
    """ავტომობილის ზოგადი ინფო NHTSA-დან"""
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            res = response.json()['Results'][0]
            return res if res.get("Make") else None
    except: return None

def scan_vin_strict(image_bytes):
    """Google Vision-ით VIN-ის ამოცნობა"""
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        response = requests.post(url, json=payload, timeout=15)
        result = response.json()
        if 'responses' in result and result['responses'][0].get('textAnnotations'):
            full_text = result['responses'][0]['textAnnotations'][0]['description']
            for block in full_text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17 and is_valid_vin(clean): return clean
    except: pass
    return None

def get_bid_cars_images(vin):
    """სურათების ამოღება bid.cars-დან"""
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
                    full_img = src.replace("-thumbnail", "").replace("-small", "")
                    if full_img not in image_links: image_links.append(full_img)
    except: pass
    return image_links

# --- გვერდების მართვა ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - Smart Hub")
    file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])
    if file:
        st.image(file, width=300)
        if st.button("ანალიზის დაწყება", use_container_width=True):
            with st.spinner("მიმდინარეობს დამუშავება..."):
                vin = scan_vin_strict(file.getvalue())
                if vin:
                    st.session_state['active_vin'] = vin
                    st.session_state['details'] = get_vin_details(vin)
                    st.session_state['images'] = get_bid_cars_images(vin)
                    st.session_state['page'] = 'analysis'
                    st.rerun()
                else:
                    st.error("❌ VIN კოდი ვერ ამოიცნო.")

elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    details = st.session_state.get('details')
    imgs = st.session_state.get('images', [])

    if st.button("⬅️ უკან"):
        st.session_state['page'] = 'home'
        st.rerun()

    st.success(f"✅ ამოცნობილია: {vin}")
    
    if details:
        st.header(f"📋 {details.get('ModelYear')} {details.get('Make')} {details.get('Model')}")
    
    st.divider()

    # სურათების გალერეა
    st.subheader("🖼️ აუქციონის ფოტოები")
    if imgs:
        cols = st.columns(3)
        for i, url in enumerate(imgs):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("⚠️ სურათები bid.cars-ზე ვერ მოიძებნა.")
        st.link_button("იხილეთ Google-ის შედეგები", f"https://www.google.com/search?q={vin}")

    st.divider()
    
    # სწრაფი ბმულები
    st.subheader("🔍 სწრაფი ბმულები")
    c1, c2, c3 = st.columns(3)
    with c1: st.link_button("🖼️ BidFax", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}", use_container_width=True)
    with c2: st.link_button("📊 Carfax", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
    with c3: st.link_button("📜 PLC.ua", f"https://plc.ua/ca/vin-check/?vin={vin}", use_container_width=True)
