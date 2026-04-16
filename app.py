import streamlit as st
import requests
import base64
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="Car Damage AI Expert", layout="wide")

# შენი API გასაღებები
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None

def scan_vin(image_bytes):
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload).json()
        text = res['responses'][0]['textAnnotations'][0]['description']
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except: return None

def get_ai_expert_analysis(images):
    """ეს ფუნქცია აგენერირებს ზუსტად იმ დასკვნას, რაც მოგეწონათ"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    image_parts = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img.getvalue()).decode('utf-8')}} for img in images]

    prompt_text = """
    შენ ხარ პროფესიონალი ავტო-ექსპერტი. მოწოდებული ფოტოების საფუძველზე შეადგინე მანქანის დაზიანების დეტალური დასკვნა ქართულ ენაზე.
    გამოიყენე ზუსტად ეს სტრუქტურა:

    ### 📝 ავტომობილის ვიზუალური ექსპერტიზა
    * **ხილული დაზიანებები:** (აღწერე დეტალურად ყველა დეტალი)
    * **დარტყმის სიმძლავრე და შასი (Frame):** (შეაფასე დარტყმის ძალა და ლანჟერონების მდგომარეობა)
    * **მექანიკური ნაწილები და სითხეები:** (აღწერე რადიატორები და სხვა აგრეგატები)
    * **უსაფრთხოება და დამალული რისკები:** (შეაფასე აირბაგები და სავარაუდო ხარჯი)

    ---
    ### 💡 რეკომენდაცია
    (დაწერე საბოლოო აზრი აღდგენის სირთულეზე)
    """

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
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        return "AI-მ ვერ შეძლო სურათის წაკითხვა. სცადეთ სხვა ფოტო."
    except Exception as e:
        return f"შეცდომა: {str(e)}"

# --- UI ---
if st.session_state.step == 1:
    st.title("🔎 VIN ამოცნობა")
    file = st.file_uploader("ატვირთეთ VIN ფოტო", type=['jpg', 'png'])
    if file and st.button("გაგრძელება"):
        vin = scan_vin(file.getvalue())
        if vin:
            st.session_state.vin = vin
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    st.title(f"🚗 VIN: {st.session_state.vin}")
    
    col1, col2 = st.columns(2)
    col1.link_button("📊 BidFax", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    col2.link_button("🌐 Google", f"https://www.google.com/search?q={st.session_state.vin}")

    st.divider()
    st.subheader("📸 დაზიანების ექსპერტიზა")
    photos = st.file_uploader("ატვირთეთ აუქციონის ფოტოები", accept_multiple_files=True)
    
    if photos and st.button("ანალიზის დაწყება"):
        with st.spinner("AI მუშაობს დასკვნაზე..."):
            report = get_ai_expert_analysis(photos)
            st.markdown(report)

    if st.button("თავიდან დაწყება"):
        st.session_state.step = 1
        st.rerun()
