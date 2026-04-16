import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="VIN AI Pro - v2.3", page_icon="🚗", layout="wide")

# KeyError პრევენცია
if 'page' not in st.session_state: st.session_state['page'] = 'home'

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def scan_vin(image_bytes):
    """ამოიცნობს VIN-ს ფოტოდან Google Vision-ით"""
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

def parse_lot_page(url):
    """ასკანირებს პირდაპირ ლოტის გვერდს"""
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&javascript=true&url={url}"
    data = {"images": [], "info": {}}
    try:
        res = requests.get(proxy_url, timeout=40)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # სურათების ძებნა
            for img in soup.find_all('img', src=True):
                src = img['src']
                if "uploads" in src or "b-cdn.net" in src:
                    full_url = src if src.startswith('http') else "https://bidfax.info" + src
                    if full_url not in data["images"]: data["images"].append(full_url)
            # მონაცემების ამოღება (ფასი, გარბენი)
            text = soup.get_text()
            price = re.search(r'ставка: \$(\d+)', text)
            mileage = re.search(r'Пробег: ([\d\s]+)', text)
            if price: data["info"]["ფასი"] = f"${price.group(1)}"
            if mileage: data["info"]["გარბენი"] = f"{mileage.group(1).strip()} mi"
    except: pass
    return data

# --- მთავარი გვერდი ---
if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro")
    tab1, tab2 = st.tabs(["📸 VIN ფოტო სკანერი", "🔗 პირდაპირი ლოტის ანალიზი"])
    
    with tab1:
        file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])
        if file:
            st.image(file, width=300)
            if st.button("მოძებნე აუქციონზე", use_container_width=True):
                vin = scan_vin(file.getvalue())
                if vin:
                    st.success(f"ამოცნობილია: {vin}")
                    # ვაჩვენებთ ძებნის ბმულებს, რათა მომხმარებელმა იპოვოს ლოტი
                    st.markdown(f"### 🔍 აირჩიეთ აუქციონი საძიებლად:")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.link_button("🌐 Google Search", f"https://www.google.com/search?q={vin}+auction+copart+iaai")
                    with c2:
                        st.link_button("🖼️ BidFax Search", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}")
                    st.info("იპოვეთ მანქანის გვერდი, დააკოპირეთ ლინკი და ჩაასვით 'პირდაპირი ლოტის ანალიზში'.")
                else:
                    st.error("❌ VIN ვერ ამოიცნო. სცადეთ სხვა ფოტო.")

    with tab2:
        st.write("ჩაასვით აუქციონის (BidFax) გვერდის ლინკი დეტალური ანალიზისთვის")
        target_link = st.text_input("ლოტის მისამართი (URL):")
        if st.button("ანალიზის დაწყება", use_container_width=True):
            if target_link:
                with st.spinner("მიმდინარეობს გვერდის სკანირება..."):
                    st.session_state['result_data'] = parse_lot_page(target_link)
                    st.session_state['active_vin'] = target_link.split('/')[-1] # დროებითი ID
                    st.session_state['page'] = 'analysis'
                    st.rerun()

# --- ანალიზის გვერდი ---
elif st.session_state['page'] == 'analysis':
    st.button("⬅️ უკან", on_click=lambda: st.session_state.update({"page": 'home'}))
    res = st.session_state.get('result_data', {"images": [], "info": {}})
    
    if res["info"]:
        cols = st.columns(len(res["info"]))
        for i, (key, val) in enumerate(res["info"].items()):
            cols[i].metric(key, val)

    if res["images"]:
        st.subheader(f"🖼️ ნაპოვნია {len(res['images'])} ფოტო")
        cols = st.columns(3)
        for i, url in enumerate(res["images"]):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("სურათები ვერ ამოიკითხა. შეამოწმეთ ლინკის სისწორე.")


def parse_lot_page(url):
    """ასკანირებს პირდაპირ ლოტის გვერდს გაუმჯობესებული ფილტრებით"""
    # აუცილებელია JavaScript ტოკენის გამოყენება Crawlbase-დან
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&javascript=true&url={url}"
    data = {"images": [], "info": {}}
    
    try:
        res = requests.get(proxy_url, timeout=45)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. სურათების ამოღება - ვეძებთ ყველა სავარაუდო წყაროს
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') # ზოგიერთი საიტი იყენებს lazy-load-ს
                if src and ("uploads" in src or "b-cdn.net" in src):
                    full_url = src if src.startswith('http') else "https://bidfax.info" + src
                    if full_url not in data["images"]:
                        data["images"].append(full_url)
            
            # 2. ინფორმაციის ამოღება კონკრეტული კლასებიდან (თუ არსებობს)
            # BidFax-ზე მონაცემები ხშირად <li> ან <div> ტეგებშია
            full_text = soup.get_text()
            
            # ფასის ძებნა (სხვადასხვა ვარიაცია)
            price_match = re.search(r'ставка: \$(\d+)', full_text) or re.search(r'Price: \$(\d+)', full_text)
            if price_match:
                data["info"]["აუქციონის ფასი"] = f"${price_match.group(1)}"
            
            # გარბენის ძებნა
            mileage_match = re.search(r'Пробег: ([\d\s]+)', full_text) or re.search(r'Mileage: ([\d\s]+)', full_text)
            if mileage_match:
                data["info"]["გარბენი"] = f"{mileage_match.group(1).strip()} mi"

            # VIN-ის ამოღება პირდაპირ გვერდიდან (დამატებითი გადამოწმებისთვის)
            vin_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', full_text.upper())
            if vin_match:
                data["info"]["VIN"] = vin_match.group(0)

    except Exception as e:
        st.error(f"სკანირების შეცდომა: {e}")
    
    return data
