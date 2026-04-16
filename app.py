import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup

# --- კონფიგურაცია და შეცდომების თავიდან აცილება ---
st.set_page_config(page_title="VIN AI Pro - v2.2", page_icon="🚗", layout="wide")

# KeyError-ის პრევენცია
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
CRAWLBASE_TOKEN = "ytg_Gb7SMVGtgq4sUy36Hw"

def parse_lot_page(url):
    """პირდაპირი ლინკიდან ინფორმაციის ამოღება"""
    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&javascript=true&url={url}"
    data = {"images": [], "info": {}}
    
    try:
        res = requests.get(proxy_url, timeout=40)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # სურათების ამოღება
            for img in soup.find_all('img', src=True):
                src = img['src']
                if "uploads" in src or "b-cdn.net" in src:
                    full_url = src if src.startswith('http') else "https://bidfax.info" + src
                    if full_url not in data["images"]: data["images"].append(full_url)
            
            # ტექსტური მონაცემების ამოკრეფა
            text = soup.get_text()
            price = re.search(r' ставка: \$(\d+)', text)
            mileage = re.search(r'Пробег: ([\d\s]+)', text)
            if price: data["info"]["ფასი"] = f"${price.group(1)}"
            if mileage: data["info"]["გარბენი"] = f"{mileage.group(1).strip()} mi"
    except: pass
    return data

# --- UI ---
if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - Deep Link Analysis")
    
    tab1, tab2 = st.tabs(["📸 VIN ფოტო სკანერი", "🔗 პირდაპირი ლოტის ანალიზი"])
    
    with tab1:
        file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])
        if file:
            st.image(file, width=250)
            if st.button("მოძებნე აუქციონზე"):
                # VIN-ის ამოცნობის და ძებნის ლოგიკა აქ...
                pass

    with tab2:
        st.info("იპოვეთ მანქანა BidFax-ზე ან bid.cars-ზე და ჩაასვით ლინკი ქვემოთ")
        target_link = st.text_input("ჩაასვით ლოტის მისამართი:", placeholder="https://bidfax.info/...")
        
        if st.button("ამ გვერდის გაანალიზება", use_container_width=True):
            if target_link:
                with st.spinner("მიმდინარეობს გვერდის სკანირება..."):
                    st.session_state['result_data'] = parse_lot_page(target_link)
                    st.session_state['active_vin'] = "LINK_SEARCH"
                    st.session_state['page'] = 'analysis'
                    st.rerun()

elif st.session_state['page'] == 'analysis':
    st.button("⬅️ უკან", on_click=lambda: st.session_state.update({"page": 'home'}))
    res = st.session_state.get('result_data', {"images": [], "info": {}})
    
    if res["info"]:
        st.subheader("📊 აუქციონის მონაცემები")
        c1, c2 = st.columns(2)
        if "ფასი" in res["info"]: c1.metric("ფასი", res["info"]["ფასი"])
        if "გარბენი" in res["info"]: c2.metric("გარბენი", res["info"]["გარბენი"])

    st.subheader("🖼️ სურათები პირდაპირ გვერდიდან")
    if res["images"]:
        cols = st.columns(3)
        for i, url in enumerate(res["images"]):
            cols[i % 3].image(url, use_container_width=True)
    else:
        st.warning("მოცემულ ლინკზე სურათები ვერ მოიძებნა.")
