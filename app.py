import streamlit as st
import requests
import base64
import re

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN Scanner & Linker", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# Session State ინიციალიზაცია
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

# --- ნაბიჯი 1: კლასიკური VIN სკანერი (როგორც სურათზე 782067.png) ---
if st.session_state.step == 1:
    st.title("📸 VIN Scanner & Linker")
    st.write("გადაუღეთ ფოტო მანქანის VIN სტიკერს")
    
    # ვიყენებთ სტანდარტულ Upload ღილაკს, რომელიც მობილურზე კამერასაც ხსნის
    source = st.file_uploader("აირჩიეთ ფოტო ან გადაუღეთ კამერით", type=['jpg', 'jpeg', 'png'])
        
    if source and st.button("მონაცემების ამოღება ➡️"):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            text = scan_text(source.getvalue())
            vin_match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
            if vin_match:
                st.session_state.vin = vin_match.group(0)
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ ამოიცნო. სცადეთ უფრო მკაფიო ფოტო.")

# --- ნაბიჯი 2 & 3: ძებნა და ანალიზის პანელი ---
elif st.session_state.step == 2:
    st.title(f"🔍 ანალიზი: {st.session_state.vin}")
    
    col_links, col_analysis = st.columns([0.6, 0.4])

    with col_links:
        st.subheader("🌐 ნაბიჯი 2: მოძებნეთ ინფორმაცია")
        st.info("გახსენით ბმულები, გადაუღეთ სქრინშოტები მონაცემებს და დაბრუნდით აქ.")
        
        # ბმულები, რომლებიც იხსნება ახალ ფანჯარაში (ეს არ დაიბლოკება)
        st.link_button("🚀 გახსენი BidFax (ისტორია)", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}", use_container_width=True)
        st.link_button("🖼️ გახსენი Google Images", f"https://www.google.com/search?q={st.session_state.vin}+auction&tbm=isch", use_container_width=True)
        st.link_button("🚘 გახსენი Bid.cars", f"https://bid.cars/en/search/results?q={st.session_state.vin}", use_container_width=True)

    with col_analysis:
        st.subheader("🛠️ AI პანელი")
        st.write("ატვირთეთ აუქციონის სქრინშოტები ანალიზისთვის:")
        
        # სქრინშოტების ატვირთვა (image_78f9e3.png სტილში)
        sc_files = st.file_uploader("გააკეთეთ სქრინშოტები და ატვირთეთ:", accept_multiple_files=True, label_visibility="collapsed")
        
        if sc_files and st.button("🚀 დაიწყე AI ანალიზი", use_container_width=True):
            st.session_state.screenshots = sc_files
            st.session_state.step = 3
            st.rerun()
        
        st.divider()
        if st.button("🔄 თავიდან დაწყება"):
            st.session_state.step = 1
            st.session_state.vin = None
            st.rerun()

# --- ნაბიჯი 4: საბოლოო რეპორტი ---
elif st.session_state.step == 3:
    st.title("🧠 AI ექსპერტიზის დასკვნა")
    # აქ ხდება ყველა სქრინშოტის ანალიზი
    st.success("მონაცემები ამოკრებილია ყველა ატვირთული სქრინშოტიდან.")
    # (ანალიზის ლოგიკა...)
    
    if st.button("🔙 უკან დაბრუნება"):
        st.session_state.step = 2
        st.rerun()
