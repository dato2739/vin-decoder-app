import streamlit as st
import requests
import base64
import re
import json

# --- კონფიგურაცია ---
st.set_page_config(page_title="Car Auction Expert AI", layout="wide")

# API გასაღებები
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None

# --- ფუნქციები ---

def extract_text_from_image(image_bytes):
    """Google Vision API ტექსტის ამოსაცნობად"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": encoded},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        res_json = response.json()
        if 'responses' in res_json and res_json['responses'][0]:
            return res_json['responses'][0]['textAnnotations'][0]['description']
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def get_gemini_analysis(raw_text):
    """Gemini AI ტექსტური მონაცემების ანალიზისთვის"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    შენ ხარ ავტო-ექსპერტი. გააანალიზე აუქციონის მონაცემები და დაწერე დეტალური დასკვნა ქართულად.
    მონაცემები: {raw_text}
    
    აუცილებლად მოიცვი:
    1. ავტომობილის მოდელი და წელი.
    2. დაზიანების ტიპი (მაგ: Front End) და მისი სირთულე.
    3. გარბენის შეფასება (Odometer).
    4. სტატუსი (Rebuildable/Starts) და რას ნიშნავს ეს მყიდველისთვის.
    5. რეკომენდაცია: ღირს თუ არა ყიდვა.
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "AI-მ ვერ დაამუშავა ტექსტი. შეამოწმეთ API კვოტა."
    except Exception as e:
        return f"შეცდომა კავშირისას: {str(e)}"

# --- ინტერფეისი ---

st.title("🚗 Car Auction Expert AI")

if st.session_state.step == 1:
    st.header("🔎 ნაბიჯი 1: VIN-ის ამოცნობა")
    st.write("ატვირთეთ ფოტო, სადაც ჩანს VIN კოდი.")
    vin_file = st.file_uploader("აირჩიეთ ფაილი", type=['jpg', 'jpeg', 'png'], key="vin_up")
    
    if vin_file and st.button("ამოცნობა"):
        with st.spinner("მიმდინარეობს VIN-ის ძებნა..."):
            extracted = extract_text_from_image(vin_file.getvalue())
            match = re.search(r'[A-Z0-9]{17}', str(extracted).upper().replace('O', '0'))
            if match:
                st.session_state.vin = match.group(0)
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ მოიძებნა. სცადეთ უფრო მკაფიო ფოტო.")

elif st.session_state.step == 2:
    st.header(f"📊 მონაცემების ანალიზი: {st.session_state.vin}")
    
    # სწრაფი ძებნის ღილაკები
    col1, col2, col3 = st.columns(3)
    col1.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    col2.link_button("🚘 Bid.cars აუქციონი", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
    col3.link_button("🔍 Google ძიება", f"https://www.google.com/search?q={st.session_state.vin}")

    st.divider()
    
    st.subheader("📝 აუქციონის ფურცლის ექსპერტიზა")
    st.write("ატვირთეთ აუქციონის მონაცემების სქრინშოტი")
    
    auc_file = st.file_uploader("აირჩიეთ სქრინი", type=['jpg', 'jpeg', 'png'], key="auc_up")
    
    if auc_file and st.button("ანალიზის დაწყება"):
        with st.spinner("AI ამუშავებს მონაცემებს..."):
            raw_info = extract_text_from_image(auc_file.getvalue())
            if raw_info:
                report = get_gemini_analysis(raw_info)
                st.info("### 📑 ექსპერტის დასკვნა:")
                st.markdown(report)
            else:
                st.error("სურათიდან ტექსტის ამოკითხვა ვერ მოხერხდა.")

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.session_state.vin = None
        st.rerun()
