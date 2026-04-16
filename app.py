import streamlit as st
import requests
import base64
import re

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN AI Investigator", layout="wide", initial_sidebar_state="collapsed")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# Session State-ის დაზუსტება შეცდომების თავიდან ასაცილებლად
if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None

def scan_text(image_bytes):
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        return res['responses'][0]['textAnnotations'][0]['description']
    except: return ""

# --- ეტაპი 1: ძველი აპის სტილი (VIN სკანერი) ---
if st.session_state.step == 1:
    st.title("📸 ნაბიჯი 1: VIN სკანერი")
    st.write("გადაუღეთ ფოტო მანქანის VIN სტიკერს")
    
    # კამერის პირდაპირი წვდომა
    source = st.camera_input("დაასკანირეთ VIN")
    if not source:
        source = st.file_uploader("ან აირჩიეთ ფოტო გალერეიდან", type=['jpg', 'jpeg', 'png'])
        
    if source and st.button("მონაცემების ამოღება ➡️", use_container_width=True):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            text = scan_text(source.getvalue())
            # VIN-ის ძებნა ტექსტში
            vin_match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
            if vin_match:
                st.session_state.vin = vin_match.group(0)
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ ამოიცნო. სცადეთ უფრო მკაფიო ფოტო.")

# --- ეტაპი 2: ციფრული VIN და სწრაფი ლინკები ---
elif st.session_state.step == 2:
    st.title("🔗 ნაბიჯი 2: მოძებნე აუქციონზე")
    st.success(f"ამოცნობილია VIN: **{st.session_state.vin}**")
    
    st.subheader("გადადით ბმულებზე ინფორმაციის სანახავად:")
    col1, col2, col3 = st.columns(3)
    
    # Google Images საუკეთესოა სწრაფი დათვალიერებისთვის
    col1.link_button("🔍 Google Images", f"https://www.google.com/search?q={st.session_state.vin}+auction&tbm=isch")
    # BidFax ისტორიისთვის
    col2.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    col3.link_button("🚘 Bid.cars", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
    
    st.divider()
    if st.button("გადავიდეთ ანალიზის სივრცეში ➡️", use_container_width=True):
        st.session_state.step = 3
        st.rerun()

# --- ეტაპი 3: გაფართოებული სამუშაო სივრცე (ინტეგრირებული) ---
elif st.session_state.step == 3:
    # მაქსიმალური სივრცე აუქციონისთვის, მცირე პანელი ანალიზისთვის
    col_auction, col_tools = st.columns([0.8, 0.2]) 
    
    with col_auction:
        st.subheader("🌐 აუქციონის დათვალიერება")
        auction_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}"
        st.components.v1.iframe(auction_url, height=800, scrolling=True)

    with col_tools:
        st.markdown("### 🛠️ AI პანელი")
        st.caption(f"VIN: {st.session_state.vin}")
        
        st.write("გააკეთეთ სქრინშოტები და ატვირთეთ:")
        # სქრინშოტების სწრაფი მიწოდება
        sc_files = st.file_uploader("Upload SC", accept_multiple_files=True, label_visibility="collapsed")
        
        if sc_files and st.button("🚀 AI ანალიზი", use_container_width=True):
            st.session_state.screenshots = sc_files
            st.session_state.step = 4
            st.rerun()
        
        if st.button("🔄 თავიდან დაწყება"):
            st.session_state.step = 1
            st.rerun()

# --- ეტაპი 4: საბოლოო ანალიზი ---
elif st.session_state.step == 4:
    st.title("🧠 AI ექსპერტიზის დასკვნა")
    # აქ ხდება ყველა სქრინშოტის ტექსტის შეჯამება და ანალიზი
    st.info("მონაცემები მუშავდება...")
    if st.button("🔙 დაბრუნება სამუშაო სივრცეში"):
        st.session_state.step = 3
        st.rerun()
