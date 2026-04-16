import streamlit as st
import requests
import base64
import json
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="Car History & Damage AI", layout="wide", page_icon="🚗")

# API გასაღებები
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

# სესიის ინიციალიზაცია
if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None
if 'analysis_report' not in st.session_state: st.session_state.analysis_report = None

# --- ფუნქციები ---

def scan_vin(image_bytes):
    """Google Vision API VIN-ის ციფრულ ფორმატში გადასაყვანად"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        text = res['responses'][0]['textAnnotations'][0]['description']
        # ეძებს 17-ნიშნა კომბინაციას
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except: return None

def analyze_damage(images):
    """Gemini 1.5 Flash - დაზიანების დეტალური ვიზუალური ანალიზი"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    image_parts = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img.getvalue()).decode('utf-8')}} for img in images]

    prompt_text = """
    შეასრულე ავტომობილის დაზიანების პროფესიონალური ექსპერტიზა ფოტოების მიხედვით:
    1. ჩამოთვალე ყველა ხილული დაზიანება (ბამპერი, ფარები, კაპოტი, შუშა და ა.შ.).
    2. შეაფასე დარტყმის სიმძლავრე და სავარაუდო გავლენა შასიზე (Frame/Chassis).
    3. ყურადღება მიაქციე დეტალებს: აირბაგები, სითხეების გაჟონვა, გეომეტრიის დარღვევა.
    4. შეაფასე, ხომ არ ჩანს "მალული" დაზიანების კვალი ან არაპროფესიონალური ჩარევა.
    პასუხი დააბრუნე ქართულად, მკაფიო პუნქტებად.
    """

    payload = {"contents": [{"parts": [*image_parts, {"text": prompt_text}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "ანალიზი ვერ მოხერხდა. სცადეთ სხვა ფოტოები."
    except Exception as e:
        return f"შეცდომა: {str(e)}"

# --- ინტერფეისი ---

# ნაბიჯი 1: VIN ატვირთვა
if st.session_state.step == 1:
    st.title("🔎 ნაბიჯი 1: VIN კოდის ამომცნობი")
    st.info("ატვირთეთ ფოტო, სადაც მკაფიოდ ჩანს VIN კოდი (მაგ. საქარე მინაზე ან კარიზე).")
    file = st.file_uploader("აირჩიეთ ფაილი", type=['jpg', 'jpeg', 'png'])
    
    if file and st.button("ამოცნობა და გაგრძელება ➡️"):
        with st.spinner("მიმდინარეობს დამუშავება..."):
            vin_code = scan_vin(file.getvalue())
            if vin_code:
                st.session_state.vin = vin_code
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ ამოიცნო. სცადეთ სხვა ფოტო.")

# ნაბიჯი 2: ძირითადი ინფორმაცია და ანალიზი
elif st.session_state.step == 2:
    st.title(f"🚗 ავტომობილის პასპორტი: {st.session_state.vin}")
    
    # ინფორმაცია და ლინკები
    st.subheader("🌐 ძიება და ისტორია")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
    with col2:
        st.link_button("🚘 Bid.cars აუქციონი", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
    with col3:
        st.link_button("🔍 Google ძიება", f"https://www.google.com/search?q={st.session_state.vin}")

    st.divider()

    # დაზიანების ანალიზის სექცია
    st.subheader("📸 ნაბიჯი 2: დაზიანების AI ექსპერტიზა")
    st.write("ატვირთეთ აუქციონის ფოტოები ან სქრინშოტები დეტალური ანალიზისთვის.")
    
    scs = st.file_uploader("ამოირჩიეთ სურათები", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
    
    if scs:
        if st.button("დაზიანების ანალიზის დაწყება 🔥"):
            with st.spinner("ხელოვნური ინტელექტი აანალიზებს ფოტოებს..."):
                st.session_state.analysis_report = analyze_damage(scs)

    # შედეგის ჩვენება
    if st.session_state.analysis_report:
        st.info("### 📝 AI დასკვნა დაზიანებების შესახებ:")
        st.markdown(st.session_state.analysis_report)
        st.divider()

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.session_state.vin = None
        st.session_state.analysis_report = None
        st.rerun()
