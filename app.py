import streamlit as st
import requests
import base64
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="Car History Expert", layout="wide")

VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None

# --- ფუნქციები ---

def scan_text_from_image(image_bytes):
    """ამოიღებს ტექსტს აუქციონის სქრინიდან"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload).json()
        return res['responses'][0]['textAnnotations'][0]['description']
    except: return None

def get_expert_report(raw_text):
    """ტექსტური მონაცემების საფუძველზე აკეთებს დასკვნას"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    გააანალიზე აუქციონის მონაცემები და დაწერე პროფესიონალური დასკვნა ქართულად:
    მონაცემები: {raw_text}
    
    დასკვნაში აუცილებლად შეიტანე:
    1. ავტომობილის მონაცემები (მარკა, მოდელი, წელი - თუ ჩანს).
    2. გარბენის შეფასება (Odometer).
    3. დაზიანების ტიპი (Primary Damage) და სტატუსი (Sale Document).
    4. რისკები: რამდენად საშიშია ეს დაზიანება (მაგ: Front End Collision).
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except: return "ანალიზი ვერ მოხერხდა."

# --- ინტერფეისი ---

if st.session_state.step == 1:
    st.title("🔎 ნაბიჯი 1: VIN კოდის ამოცნობა")
    file = st.file_uploader("ატვირთეთ VIN-ის ფოტო", type=['jpg', 'png'])
    if file and st.button("გაგრძელება"):
        text = scan_text_from_image(file.getvalue())
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        if match:
            st.session_state.vin = match.group(0)
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    st.title(f"🚗 ავტომობილის პასპორტი: {st.session_state.vin}")
    
    # სწრაფი ლინკები
    c1, c2, c3 = st.columns(3)
    c1.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    c2.link_button("🚘 Bid.cars აუქციონი", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
    c3.link_button("🔍 Google ძიება", f"https://www.google.com/search?q={st.session_state.vin}")

    st.divider()
    st.subheader("📝 ნაბიჯი 2: აუქციონის მონაცემების ანალიზი")
    st.write("ატვირთეთ აუქციონის მონაცემების სქრინშოტი")
    
    auc_file = st.file_uploader("აირჩიეთ სქრინი", type=['jpg', 'png'])
    if auc_file and st.button("მონაცემების დამუშავება"):
        with st.spinner("AI კითხულობს მონაცემებს..."):
            raw_info = scan_text_from_image(auc_file.getvalue())
            report = get_expert_report(raw_info)
            st.markdown("### 📝 ექსპერტის დასკვნა:")
            st.write(report)

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.rerun()
