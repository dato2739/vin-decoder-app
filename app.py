import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="VIN AI Pro - v2.0", page_icon="🚗", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def get_bidfax_lot_images(vin):
    """
    ჯერ პოულობს კონკრეტული ლოტის ლინკს, შემდეგ კი სურათებს
    """
    search_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
    proxy_base = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&javascript=true&url="
    
    images = []
    car_info = {}

    try:
        # 1. ვეძებთ ლოტის პირდაპირ ბმულს ძებნის შედეგებში
        search_res = requests.get(proxy_base + requests.utils.quote(search_url), timeout=30)
        if search_res.status_code == 200:
            soup = BeautifulSoup(search_res.text, 'html.parser')
            
            # ვეძებთ პირველივე ლინკს, რომელიც შეიცავს VIN-ს და .html-ს
            lot_link = None
            for a in soup.find_all('a', href=True):
                if vin.lower() in a['href'].lower() and ".html" in a['href']:
                    lot_link = a['href']
                    break
            
            # 2. თუ ლოტის ბმული ნაპოვნია, შევდივართ მასში
            target_url = lot_link if lot_link else search_url
            lot_res = requests.get(proxy_base + requests.utils.quote(target_url), timeout=30)
            
            if lot_res.status_code == 200:
                lot_soup = BeautifulSoup(lot_res.text, 'html.parser')
                
                # სურათების ამოღება (ვეძებთ დიდ სურათებს)
                for a in lot_soup.find_all('a', href=True):
                    href = a['href']
                    if "uploads" in href and (".jpg" in href or ".jpeg" in href):
                        full_url = href if href.startswith('http') else "https://bidfax.info" + href
                        if full_url not in images:
                            images.append(full_url)
                
                # თუ სურათები <a> ტეგში არაა, ვეძებთ <img>-ში
                if not images:
                    for img in lot_soup.find_all('img', src=True):
                        src = img['src']
                        if "uploads" in src:
                            full_url = src if src.startswith('http') else "https://bidfax.info" + src
                            if full_url not in images:
                                images.append(full_url)

                # ინფორმაციის წამოღება (ფასი, გარბენი)
                text = lot_soup.get_text()
                price = re.search(r' ставка: \$(\d+)', text)
                mileage = re.search(r'Пробег: ([\d\s]+)', text)
                if price: car_info["ფასი"] = f"${price.group(1)}"
                if mileage: car_info["გარბენი"] = f"{mileage.group(1).strip()} mi"

    except Exception as e:
        st.error(f"კავშირის შეცდომა: {e}")
        
    return images, car_info

# --- სტანდარტული VIN სკანერი ---
def scan_vin(image_bytes):
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    res = requests.post(url, json=payload).json()
    if 'responses' in res and res['responses'][0].get('textAnnotations'):
        text = res['responses'][0]['textAnnotations'][0]['description']
        for block in text.upper().replace('O', '0').split():
            clean = re.sub(r'[^A-Z0-9]', '', block)
            if len(clean) == 17: return clean
    return None

# --- UI ---
if 'page' not in st.session_state: st.session_state['page'] = 'home'

if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro v2.0")
    file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])
    if file:
        st.image(file, width=300)
        if st.button("ღრმა ძიების დაწყება (BidFax Direct)", use_container_width=True):
            vin = scan_vin(file.getvalue())
            if vin:
                st.session_state['active_vin'] = vin
                with st.spinner(f"ვეძებ ლოტს {vin}-ისთვის..."):
                    imgs, info = get_bidfax_lot_images(vin)
                    st.session_state['data'] = {"images": imgs, "info": info}
                st.session_state['page'] = 'analysis'
                st.rerun()

elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    data = st.session_state.get('data', {"images": [], "info": {}})
    
    st.button("⬅️ უკან", on_click=lambda: st.session_state.update({"page": 'home'}))
    st.header(f"🔍 VIN: {vin}")

    if data["info"]:
        c1, c2 = st.columns(2)
        if "ფასი" in data["info"]: c1.metric("აუქციონის ფასი", data["info"]["ფასი"])
        if "გარბენი" in data["info"]: c2.metric("გარბენი", data["info"]["გარბენი"])

    st.subheader("🖼️ აუქციონის ფოტოები")
    if data["images"]:
        cols = st.columns(3)
        for i, url in enumerate(data["images"]):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("სურათები ვერ მოიძებნა. შესაძლოა Crawlbase-ის ლიმიტი ან ბლოკი.")

    st.divider()
    st.link_button("გახსენი ორიგინალი გვერდი", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}")
