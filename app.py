import streamlit as st
import requests
import base64
import json
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="Car AI Investigator PRO", layout="wide")

VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None
if 'analysis_report' not in st.session_state: st.session_state.analysis_report = None

# --- ფუნქციები ---

def scan_vin(image_bytes):
    """Google Vision API VIN-ისთვის"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload).json()
        text = res['responses'][0]['textAnnotations'][0]['description']
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except: return None

def analyze_damage(images):
    """Gemini 1.5 Flash - დეტალური ექსპერტიზა უსაფრთხოების ფილტრების გარეშე"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    image_parts = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img.getvalue()).decode('utf-8')}} for img in images]

    prompt_text = """
    შენ ხარ ავტო-ექსპერტი. მოწოდებული ფოტოების საფუძველზე შეადგინე მანქანის დაზიანების დეტალური დასკვნა.
    გამოიყენე შემდეგი სტრუქტურა:

    ### 📝 ავტომობილის ვიზუალური ექსპერტიზა
    
    * **ხილული დაზიანებები:** (აღწერე დეტალურად: ბამპერი, კაპოტი, ფარები და ა.შ.)
    * **დარტყმის სიმძლავრე და შასი (Frame):** (შეაფასე გავლენა ლანჟერონებზე ან ძარის გეომეტრიაზე)
    * **მექანიკური ნაწილები:** (რადიატორების და დაკიდების სისტემის მდგომარეობა)
    * **უსაფრთხოება და რისკები:** (აირბაგები და დამალული დაზიანებები)

    ---
    ### 💡 რეკომენდაცია
    (შეჯამება: რამდენად რთული იქნება აღდგენა)
    
    პასუხი დააბრუნე ქართულად.
    """

    # ეს ნაწილი თიშავს დაბლოკვებს
    payload = {
        "contents": [{"parts": [*image_parts, {"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        elif 'promptFeedback' in result:
            return f"API-მ დაბლოკა სურათი მიზეზით: {result['promptFeedback']}"
        else:
            return "ანალიზი ვერ მოხერხდა. სცადეთ მხოლოდ 1 სურათის ატვირთვა თავიდან."
    except Exception as e:
        return f"კავშირის შეცდომა: {str(e)}"

# --- ინტერფეისი ---

if st.session_state.step == 1:
    st.title("🔎 ნაბიჯი 1: VIN კოდის ამოცნობა")
    file = st.file_uploader("ატვირთეთ VIN-ის ფოტო", type=['jpg', 'jpeg', 'png'])
    if file and st.button("ამოცნობა და გაგრძელება ➡️"):
        with st.spinner("ვამუშავებ..."):
            vin_code = scan_vin(file.getvalue())
            if vin_code:
                st.session_state.vin = vin_code
                st.session_state.step = 2
                st.rerun()
            else: st.error("VIN ვერ ამოიცნო.")

elif st.session_state.step == 2:
    st.title(f"🚗 ავტომობილის პასპორტი: {st.session_state.vin}")
    
    # ლინკები
    c1, c2, c3 = st.columns(3)
    c1.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    c2.link_button("🚘 Bid.cars აუქციონი", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
    c3.link_button("🔍 Google ძიება", f"https://www.google.com/search?q={st.session_state.vin}")

    st.divider()
    st.subheader("📸 ნაბიჯი 2: დაზიანების AI ექსპერტიზა")
    scs = st.file_uploader("ატვირთეთ აუქციონის ფოტოები", accept_multiple_files=True)
    
    if scs and st.button("დაზიანების ანალიზის დაწყება 🔥"):
        with st.spinner("AI აანალიზებს ფოტოებს..."):
            st.session_state.analysis_report = analyze_damage(scs)

    if st.session_state.analysis_report:
        st.markdown(st.session_state.analysis_report)
        st.divider()

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.session_state.analysis_report = None
        st.rerun()
