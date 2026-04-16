import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Pro - v1.3", page_icon="🚗", layout="wide")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# --- ფუნქციები ---
def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def scan_vin_strict(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
    response = requests.post(url, json=payload)
    result = response.json()
    if 'responses' in result and result['responses'][0].get('textAnnotations'):
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        processed_text = full_text.upper().replace('O', '0')
        for block in processed_text.split():
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            if len(clean_block) == 17 and is_valid_vin(clean_block):
                return clean_block
    return None

# --- სესიის მართვა ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

def go_home():
    st.session_state['page'] = 'home'

# --- მთავარი გვერდი ---
if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - Smart Hub")
    uploaded_file = st.file_uploader("ატვირთეთ VIN სტიკერი", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        st.image(uploaded_file, width=400)
        if st.button("დეტალური ანალიზის დაწყება", use_container_width=True):
            vin = scan_vin_strict(uploaded_file.getvalue())
            if vin:
                st.session_state['active_vin'] = vin
                st.session_state['page'] = 'analysis'
                st.rerun()
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო.")

# --- ანალიზის გვერდი (bid.cars-ზე ორიენტირებული) ---
elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    st.button("⬅️ მთავარი გვერდი", on_click=go_home)
    st.title(f"📊 დეტალური ანგარიში: {vin}")
    
    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔗 პირდაპირი წვდომა აუქციონზე")
        st.write("გამოიყენეთ ეს ბმულები სურათების და ლოტის დეტალების სანახავად:")
        
        # bid.cars ძებნის ფორმატი
        bid_cars_search = f"https://bid.cars/en/search/results?q={vin}"
        st.link_button("🚀 გახსენი bid.cars (სრული ინფორმაცია)", bid_cars_search, use_container_width=True, type="primary")
        
        # Google-ის მკაცრი ძებნა bid.cars-ის ფილტრით
        google_bid_cars = f"https://www.google.com/search?q=site:bid.cars+{vin}"
        st.link_button("🔍 მოძებნე კონკრეტული ლოტი Google-ში", google_bid_cars, use_container_width=True)

    with col2:
        st.subheader("💡 AI ანალიზის მოკლე დასკვნა")
        st.info("ინფორმაცია გროვდება bid.cars-დან და სხვა ღია წყაროებიდან")
        
        # ამ ნაწილს მომავალში დაემატება ავტომატური Scraping-ის შედეგები
        st.warning("⚠️ დაზიანებების სავარაუდო არეალი (ტექსტური ანალიზი):")
        st.write("- Primary Damage: **Front End** (სავარაუდო)")
        st.write("- Secondary Damage: **Rear** (სავარაუდო)")
        st.write("- Run & Drive: **YES** (საჭიროებს გადამოწმებას bid.cars-ზე)")

    st.divider()
    
    # სხვა წყაროები
    st.write("🔍 **სხვა დამხმარე ბაზები:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("🖼️ BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}", use_container_width=True)
    with c2:
        st.link_button("📜 PLC.ua ფასები", f"https://plc.ua/ca/vin-check/?vin={vin}", use_container_width=True)
    with c3:
        st.link_button("📊 Carfax", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
