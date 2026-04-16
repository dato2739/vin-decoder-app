import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - All-in-One", page_icon="🚗", layout="centered")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def get_vin_details(vin):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.post(url, timeout=5) # requests.post უკეთესია API-სთვის
        if response.status_code == 200:
            res = response.json()['Results'][0]
            if not res.get("Make"): return None
            return res
    except: return None
    return None

def scan_vin_strict(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
    response = requests.post(url, json=payload)
    result = response.json()
    if 'responses' in result and result['responses'][0]:
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        processed_text = full_text.upper().replace('O', '0')
        potential_blocks = processed_text.split()
        for block in potential_blocks:
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            if len(clean_block) == 17 and is_valid_vin(clean_block):
                return clean_block
    return None

# --- ინტერფეისი ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚗 VIN AI Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280;'>Google Cloud Vision & NHTSA Decoder</p>", unsafe_allow_headers=True)
st.write("---")

uploaded_file = st.file_uploader("ატვირთეთ ფოტო, რომელიც შეიცავს VIN კოდს", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("ანალიზი და გაშიფვრა", use_container_width=True):
        with st.spinner("მიმდინარეობს ანალიზი..."):
            vin = scan_vin_strict(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ კოდი ამოცნობილია: {vin}")
                st.code(vin, language='text')
                
                details = get_vin_details(vin)
                
                if details:
                    st.markdown(f"### 📋 {details.get('ModelYear')} {details.get('Make')} {details.get('Model')}")
                    col_det1, col_det2 = st.columns(2)
                    col_det1.metric("მარკა", details.get("Make"))
                    col_det2.metric("მოდელი", details.get("Model"))
                    col_det1.metric("წელი", details.get("ModelYear"))
                    col_det2.metric("ქვეყანა", details.get("PlantCountry"))
                    st.info(f"⚙️ ძრავა: {details.get('DisplacementL')}L {details.get('EngineConfiguration')}{details.get('EngineCylinders')}")
                
                # --- ახალი ეტაპის სტრატეგია ---
                st.write("---")
                st.markdown("🔍 **მოძებნეთ აუქციონის ფოტოები და ისტორია:**")
                st.warning("🔄 (ბაზები ხშირად ბლოკავენ ავტომატურ ძებნას. თუ გვერდი ცარიელია, გამოიყენეთ 'Paste' (Ctrl+V) საძიებო ველში).")

                col_btn1, col_btn2 = st.columns(2)
                
                # სტრატეგია 1: Google Images (ყველაზე საიმედო)
                with col_btn1:
                    google_images_url = f"https://www.google.com/search?tbm=isch&q={vin}+auction+copart+iaai"
                    st.link_button("🌐 Google Images (ფოტოები)", google_images_url, use_container_width=True)
                
                # სტრატეგია 2: BidFax (პირდაპირი ლინკი)
                with col_btn2:
                    # საუკეთესო ფორმატი BidFax-ისთვის
                    bidfax_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
                    st.link_button("🖼️ BidFax აუქციონები", bidfax_url, use_container_width=True)

                col_btn3, col_btn4 = st.columns(2)
                # სტრატეგია 3: PLC (სხვა ბაზა)
                with col_btn3:
                    plc_url = f"https://plc.ua/ca/vin-check/?vin={vin}"
                    st.link_button("📜 PLC ისტორია", plc_url, use_container_width=True)
                
                # სტრატეგია 4: NHTSA (მუშაობს 100%)
                with col_btn4:
                    if details:
                        st.link_button("🛡️ NHTSA (უსაფრთხოება)", f"https://www.nhtsa.gov/recalls?vin={vin}", use_container_width=True)
                    else:
                        st.button("🛡️ NHTSA (მონაცემები არ არის)", disabled=True, use_container_width=True)
                
                # Carfax - როგორც ოფიციალური რეპორტი
                st.write("---")
                st.link_button("📊 Carfax ოფიციალური რეპორტი", f"https://www.carfax.com/vin/{vin}", use_container_width=True)

                if not vin.startswith(('1','2','3','4','5')):
                    st.info("💡 ეს კოდი ევროპული ჩანს.")
                    st.link_button("🇪🇺 AutoDNA (ევროპული ბაზა)", f"https://www.autodna.com/vin/{vin}", use_container_width=True)

            else:
                st.error("❌ ვალიდური VIN ვერ მოიძებნა. სცადეთ სხვა ფოტო.")
