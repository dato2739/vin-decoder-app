import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# ... (წინა ფუნქციები: scan_vin, get_bidfax_lot_images) ...

# --- UI განახლება ---
if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - Deep Link Scanner")
    
    # ორი არჩევანი მომხმარებელს: ფოტო ან პირდაპირი ლინკი
    tab1, tab2 = st.tabs(["📸 VIN ფოტო", "🔗 პირდაპირი ლინკი (BidFax)"])
    
    with tab1:
        file = st.file_uploader("ატვირთეთ VIN სტიკერი", type=['jpg', 'jpeg', 'png'])
        if file:
            if st.button("ფოტოს ანალიზი", use_container_width=True):
                vin = scan_vin(file.getvalue()) #
                if vin:
                    st.session_state['active_vin'] = vin
                    with st.spinner("ვეძებ ინფორმაციას..."):
                        imgs, info = get_bidfax_lot_images(vin) #
                        st.session_state['data'] = {"images": imgs, "info": info}
                    st.session_state['page'] = 'analysis'
                    st.rerun()

    with tab2:
        user_url = st.text_input("ჩაასვით BidFax-ის ლოტის ლინკი:", placeholder="https://bidfax.info/...")
        if st.button("ლინკის გაანალიზება", use_container_width=True):
            if "bidfax.info" in user_url:
                # ლინკიდან VIN-ის ამოღება ავტომატურად
                vin_match = re.search(r'vin-([a-z0-9]{17})', user_url.lower())
                vin = vin_match.group(1).upper() if vin_match else "UNKNOWN"
                
                st.session_state['active_vin'] = vin
                with st.spinner("ვკითხულობ ლინკს..."):
                    # ვიყენებთ Crawlbase-ს ამ კონკრეტულ ლინკზე
                    proxy_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&javascript=true&url={user_url}"
                    res = requests.get(proxy_url)
                    # აქედან უკვე BeautifulSoup-ით ვიღებთ სურათებს, როგორც v2.0-ში
                    # ... (შემდგომი ლოგიკა იგივეა)
                st.session_state['page'] = 'analysis'
                st.rerun()
