import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="VIN AI Pro - v1.9", page_icon="🚗", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def get_vin_data(vin):
    """BidFax-იდან დეტალური ინფორმაციის და სურათების ამოღება"""
    search_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={search_url}&javascript=true"
    
    data = {"images": [], "info": {}}
    try:
        res = requests.get(proxy_url, timeout=40)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. სურათების ძებნა (უფრო ფართო ფილტრით)
            for img in soup.find_all('img', src=True):
                src = img['src']
                if "uploads" in src or "bidfax" in src:
                    if src.startswith('/'): src = "https://bidfax.info" + src
                    if src not in data["images"]: data["images"].append(src)
            
            # 2. ინფორმაციის ამოღება (ფასი, გარბენი, დაზიანება)
            # ვეძებთ ტექსტურ ბლოკებს, რომლებიც თქვენს სქრინშოტზე ჩანს
            text_content = soup.get_text()
            price = re.search(r'Финиշ. ставка: \$(\d+)', text_content)
            mileage = re.search(r'Пробег: ([\d\s]+миль)', text_content)
            damage = re.search(r'Основное ушкодження: ([\w\s]+)', text_content)
            
            if price: data["info"]["ფასი"] = f"${price.group(1)}"
            if mileage: data["info"]["გარბენი"] = mileage.group(1)
            if damage: data["info"]["დაზიანება"] = damage.group(1)
            
    except: pass
    return data

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

# --- UI ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - Deep Scanner")
    file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])
    if file:
        st.image(file, width=300)
        if st.button("დეტალური ძიების დაწყება", use_container_width=True):
            vin = scan_vin_strict(file.getvalue())
            if vin:
                st.session_state['active_vin'] = vin
                with st.spinner("მიმდინარეობს მონაცემების სკანირება ბაზებში..."):
                    st.session_state['result_data'] = get_vin_data(vin)
                st.session_state['page'] = 'analysis'
                st.rerun()

elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    res_data = st.session_state.get('result_data', {"images": [], "info": {}})
    
    st.button("⬅️ უკან", on_click=lambda: st.session_state.update({"page": 'home'}))
    st.header(f"🔍 VIN: {vin}")

    # ინფორმაციის პანელი
    if res_data["info"]:
        st.subheader("📋 აუქციონის მონაცემები")
        cols = st.columns(len(res_data["info"]))
        for i, (key, val) in enumerate(res_data["info"].items()):
            cols[i].metric(key, val)

    st.divider()

    # სურათების გალერეა
    st.subheader("🖼️ აუქციონის ფოტოები")
    imgs = res_data.get("images", [])
    if imgs:
        st.success(f"ნაპოვნია {len(imgs)} ფოტო")
        cols = st.columns(3)
        for i, url in enumerate(imgs):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("სურათები ავტომატურად ვერ ამოიკითხა. სცადეთ პირდაპირი ბმული.")

    st.divider()
    st.link_button("ნახე BidFax-ზე (სრული გვერდი)", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}")
