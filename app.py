import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - v1 + Smart Analysis", page_icon="🚗", layout="centered")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def get_vin_details(vin):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        response = requests.get(url, timeout=5)
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

def smart_damage_analysis(vin):
    """საძიებო სისტემის მეშვეობით დაზიანებების და რისკების ანალიზი"""
    # ვიყენებთ Google-ის ძებნის სიმულაციას ინფორმაციის მოსაკრებად
    search_url = f"https://www.google.com/search?q=\"{vin}\"+damage+auction"
    
    # დაზიანების ტიპები და რისკ-ფაქტორები
    risk_factors = {
        "Flood/Water": "🌊 მაღალი რისკი: წყალში ნამყოფი (ელექტროობის პრობლემები)",
        "Frame Damage": "🏗️ კრიტიკული რისკი: გეომეტრიის დაზიანება",
        "Biohazard": "⚠️ საფრთხე: ბიოლოგიური დაზიანება სალონში",
        "Junk/Scrap": "❌ კრიტიკული: მანქანა განკუთვნილია მხოლოდ ნაწილებად",
        "Mechanical": "⚙️ რისკი: ძრავის ან გადაცემათა კოლოფის დეფექტი",
        "Side Impact": "🚗 დაზიანება: გვერდითი დარტყმა",
        "Front End": "💥 დაზიანება: წინა დარტყმა"
    }
    
    # აქ მომავალში შეგვიძლია დავაკავშიროთ რეალური Search API უფრო დეტალური ანალიზისთვის
    return risk_factors, search_url

st.title("🚗 VIN AI Pro - Smart Hub")
st.write("---")

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, use_container_width=True)
    if st.button("ანალიზი და იდენტიფიკაცია", use_container_width=True):
        with st.spinner("მიმდინარეობს დამუშავება..."):
            vin = scan_vin_strict(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ ამოცნობილია: {vin}")
                details = get_vin_details(vin)
                
                if details:
                    st.subheader(f"📋 {details.get('ModelYear')} {details.get('Make')} {details.get('Model')}")
                
                st.write("---")
                
                # --- ახალი ფუნქცია: სურათებით ანალიზი ---
                if st.button("🖼️ სურათებით ანალიზი და რისკები", use_container_width=True):
                    risks, s_url = smart_damage_analysis(vin)
                    st.markdown("### 🔍 სმარტ-ანალიზის შედეგი:")
                    st.info(f"მკაცრი ძებნა ჩართულია VIN კოდზე: `{vin}`")
                    
                    st.warning("⚠️ ყურადღება მიაქციეთ შემდეგ ტერმინებს ძებნისას:")
                    for r_name, r_desc in risks.items():
                        st.write(f"- {r_desc}")
                    
                    st.link_button("გახსენი გაფილტრული სურათები", f"https://www.google.com/search?q=\"{vin}\"&tbm=isch", use_container_width=True)

                st.write("---")
                st.write("🔍 **სწრაფი ბმულები:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    bidfax_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
                    st.link_button("🖼️ BidFax (აუქციონები)", bidfax_url, use_container_width=True)
                with col2:
                    google_url = f"https://www.google.com/search?q={vin}"
                    st.link_button("🌐 Google Search", google_url, use_container_width=True)

                col3, col4 = st.columns(2)
                with col3:
                    st.link_button("📜 PLC.ua ისტორია", f"https://plc.ua/ca/vin-check/?vin={vin}", use_container_width=True)
                with col4:
                    st.link_button("📊 Carfax რეპორტი", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
                
                if details:
                    st.write("---")
                    st.link_button("🛡️ შეამოწმეთ Recall (NHTSA)", f"https://www.nhtsa.gov/recalls?vin={vin}", use_container_width=True)
            else:
                st.error("❌ ვალიდური VIN ვერ მოიძებნა.")
