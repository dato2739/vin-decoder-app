import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

# გვერდის სათაური
st.title("🚗 VIN AI Decoder - V1 Stable")

# კონსტანტები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def scan_vin(image_bytes):
    """Google Vision-ით VIN-ის ამოცნობა"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        if 'responses' in res and res['responses'][0].get('textAnnotations'):
            text = res['responses'][0]['textAnnotations'][0]['description']
            for block in text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17: return clean
    except: pass
    return None

def get_images(vin):
    """სურათების ამოღება bid.cars-დან (V1 მეთოდი)"""
    url = f"https://bid.cars/en/search/results?q={vin}"
    proxy = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={url}&javascript=true"
    links = []
    try:
        res = requests.get(proxy, timeout=30)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for img in soup.find_all('img', src=True):
                src = img['src']
                if "b-cdn.net" in src:
                    full = src.replace("-thumbnail", "").replace("-small", "")
                    if full not in links: links.append(full)
    except: pass
    return links

# --- მთავარი ლოგიკა ---
uploaded_file = st.file_uploader("ატვირთეთ ავტომობილის VIN სტიკერი", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, caption="ატვირთული ფოტო", width=300)
    
    if st.button("მონაცემების ამოღება"):
        with st.spinner("მიმდინარეობს დამუშავება..."):
            vin = scan_vin(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ VIN კოდი: {vin}")
                
                # სურათების გამოტანა
                imgs = get_images(vin)
                if imgs:
                    st.subheader("🖼️ აუქციონის ფოტოები")
                    cols = st.columns(3)
                    for i, url in enumerate(imgs):
                        cols[i % 3].image(url, use_container_width=True)
                else:
                    st.warning("სურათები bid.cars-ზე ვერ მოიძებნა.")
                    st.link_button("ნახე BidFax-ზე", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}")
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო. სცადეთ უკეთესი ხარისხის ფოტო.")
