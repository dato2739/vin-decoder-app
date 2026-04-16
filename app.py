import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="VIN AI Pro - v1.8", page_icon="🚗", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def scan_vin_strict(image_bytes):
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
                if len(clean) == 17: return clean
    except: pass
    return None

def get_images_from_source(vin, source_type="bidcars"):
    """სურათების ამოღება სხვადასხვა წყაროდან"""
    if source_type == "bidcars":
        url = f"https://bid.cars/en/search/results?q={vin}"
    else: # BidFax ალტერნატივა
        url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
    
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={url}&javascript=true"
    image_links = []
    
    try:
        response = requests.get(proxy_url, timeout=35)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for img in soup.find_all('img', src=True):
                src = img['src']
                # ფილტრაცია წყაროს მიხედვით
                if source_type == "bidcars" and "b-cdn.net" in src:
                    full_img = src.replace("-thumbnail", "").replace("-small", "")
                    if full_img not in image_links: image_links.append(full_img)
                elif source_type == "bidfax" and "uploads" in src:
                    if src.startswith('/'): src = "https://bidfax.info" + src
                    if src not in image_links: image_links.append(src)
    except: pass
    return image_links

# --- მთავარი ლოგიკა ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - Multi-Source Search")
    file = st.file_uploader("ატვირთეთ VIN სტიკერი", type=['jpg', 'jpeg', 'png'])
    if file:
        st.image(file, width=300)
        if st.button("ანალიზის დაწყება", use_container_width=True):
            vin = scan_vin_strict(file.getvalue())
            if vin:
                st.session_state['active_vin'] = vin
                with st.spinner("ვეძებ სურათებს bid.cars-ზე..."):
                    imgs = get_images_from_source(vin, "bidcars")
                
                # თუ bid.cars-ზე არ არის, გადადის BidFax-ზე
                if not imgs:
                    with st.spinner("bid.cars ცარიელია. ვეძებ BidFax-ზე..."):
                        imgs = get_images_from_source(vin, "bidfax")
                
                st.session_state['images'] = imgs
                st.session_state['page'] = 'analysis'
                st.rerun()
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო")

elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    imgs = st.session_state.get('images', [])

    if st.button("⬅️ უკან"): 
        st.session_state['page'] = 'home'
        st.rerun()

    st.success(f"✅ VIN: {vin}")
    
    st.subheader("🖼️ ნაპოვნი ფოტოები")
    if imgs:
        cols = st.columns(3)
        for i, url in enumerate(imgs):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("⚠️ სურათები ავტომატურად ვერ მოიძებნა. გამოიყენეთ პირდაპირი ბმულები.")

    st.divider()
    
    # ღილაკები, რომლებიც მომხმარებელს დაეხმარება, თუ სკრაპერმა ვერაფერი იპოვა
    st.subheader("🔗 დამატებითი ძებნა")
    c1, c2, c3 = st.columns(3)
    with c1: st.link_button("🌐 Google Images", f"https://www.google.com/search?q=\"{vin}\"&tbm=isch", use_container_width=True)
    with c2: st.link_button("🖼️ BidFax (Manual)", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}", use_container_width=True)
    with c3: st.link_button("📊 Carfax", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
