import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN AI Pro - v1.5", page_icon="🚗", layout="wide")

# კონსტანტები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"  # თქვენი ახალი ტოკენი ჩასმულია

def scan_vin_strict(image_bytes):
    """ფოტოდან VIN კოდის ამოცნობა Google Vision-ით"""
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        if 'responses' in result and result['responses'][0].get('textAnnotations'):
            full_text = result['responses'][0]['textAnnotations'][0]['description']
            # ვეძებთ 17 სიმბოლიან კოდს
            for block in full_text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17:
                    return clean
    except Exception as e:
        st.error(f"Vision API შეცდომა: {e}")
    return None

def get_bid_cars_images(vin):
    """სურათების ამოღება bid.cars-დან Crawlbase-ის მეშვეობით"""
    search_url = f"https://bid.cars/en/search/results?q={vin}"
    # ვიყენებთ javascript=true პარამეტრს, რომ სურათები ჩაიტვირთოს
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={search_url}&javascript=true"
    
    image_links = []
    try:
        response = requests.get(proxy_url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # ვეძებთ სურათებს, რომლებიც bid.cars-ის სერვერზეა (b-cdn.net)
            for img in soup.find_all('img', src=True):
                src = img['src']
                if "b-cdn.net" in src and "photos" in src:
                    # ვცვლით thumbnail-ს მაღალი ხარისხის სურათით
                    full_img = src.replace("-thumbnail", "")
                    if full_img not in image_links:
                        image_links.append(full_img)
    except Exception as e:
        st.error(f"Scraping შეცდომა: {e}")
        
    return image_links

# --- სესიის მართვა (გვერდებს შორის ნავიგაცია) ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

def go_home():
    st.session_state['page'] = 'home'

# --- მთავარი გვერდი ---
if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - სმარტ დიაგნოსტიკა")
    st.write("ატვირთეთ ავტომობილის VIN სტიკერი სურათების მოსაძიებლად")
    
    file = st.file_uploader("აირჩიეთ ფოტო", type=['jpg', 'jpeg', 'png'])
    
    if file:
        st.image(file, width=350)
        if st.button("ანალიზის დაწყება", use_container_width=True):
            with st.spinner("მიმდინარეობს VIN კოდის ამოცნობა..."):
                vin = scan_vin_strict(file.getvalue())
                
            if vin:
                st.session_state['active_vin'] = vin
                with st.spinner("ვიძიებ აუქციონის ფოტოებს (bid.cars)..."):
                    imgs = get_bid_cars_images(vin)
                    st.session_state['auction_images'] = imgs
                st.session_state['page'] = 'analysis'
                st.rerun()
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო. სცადეთ უფრო მკაფიო ფოტო.")

# --- ანალიზის გვერდი ---
elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    st.button("⬅️ უკან დაბრუნება", on_click=go_home)
    
    st.title(f"📊 შედეგები VIN კოდისთვის: {vin}")
    st.divider()

    # სურათების გალერეა
    st.subheader("🖼️ აუქციონის ფოტოები")
    images = st.session_state.get('auction_images', [])
    
    if images:
        st.success(f"✅ ნაპოვნია {len(images)} ფოტო")
        # სურათების გამოტანა 3 სვეტად
        cols = st.columns(3)
        for idx, img_url in enumerate(images):
            with cols[idx % 3]:
                st.image(img_url, use_container_width=True)
    else:
        st.warning("სურათები bid.cars-ზე ვერ მოიძებნა. შესაძლოა ლოტი დახურულია ან სხვა საიტზეა.")
        st.link_button("მოძებნე პირდაპირ bid.cars-ზე", f"https://bid.cars/en/search/results?q={vin}")

    st.divider()
    
    # სხვა სასარგებლო ბმულები
    st.subheader("🔍 დამატებითი ბაზები")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("📜 PLC.ua ისტორია", f"https://plc.ua/ca/vin-check/?vin={vin}", use_container_width=True)
    with c2:
        st.link_button("🖼️ BidFax (არქივი)", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}", use_container_width=True)
    with c3:
        st.link_button("📊 Carfax რეპორტი", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
