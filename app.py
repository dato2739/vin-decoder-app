import streamlit as st
import requests
import base64
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="ვინ კოდით ძებნა", layout="wide")

# რუხი ფონის და მკვეთრი ღილაკების სტილი
st.markdown("""
    <style>
    /* მთლიანი გვერდის რუხი ფონი */
    .stApp {
        background-color: #2b2d33;
        color: #ffffff;
    }
    header[data-testid="stHeader"] {
        background-color: #2b2d33;
    }
    /* ტექსტის ფერები */
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }
    /* ფაილის ატვირთვის ზონა */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #3d4048;
        border: 2px dashed #ff4b2b; /* მკვეთრი ჩარჩო */
    }
    /* მკვეთრი ნარინჯისფერი ღილაკები */
    .stButton>button {
        background-color: #ff4b2b !important; /* მკვეთრი ნარინჯისფერი */
        color: white !important;
        border: none !important;
        padding: 15px 30px !important;
        font-weight: 800 !important;
        font-size: 18px !important;
        border-radius: 10px !important;
        width: 100% !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 5px 15px rgba(255, 75, 43, 0.4) !important;
        transition: 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #ff6a4d !important;
        box-shadow: 0 8px 20px rgba(255, 75, 43, 0.6) !important;
        transform: translateY(-2px);
    }
    /* ტექსტის შესაყვანი ველი */
    .stTextInput>div>div>input {
        background-color: #3d4048;
        color: #ffffff;
        border: 2px solid #64676e;
        padding: 12px;
        border-radius: 8px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #ff4b2b;
    }
    </style>
    """, unsafe_allow_html=True)

# Google Vision API გასაღები
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None

def extract_vin(image_bytes):
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
        text = res_json['responses'][0]['textAnnotations'][0]['description']
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except:
        return None

# --- ინტერფეისი ---
st.title("ვინ კოდით ძებნა")

if st.session_state.step == 1:
    st.subheader("ატვირთეთ ვინ კოდის სურათი")
    
    file = st.file_uploader("აირჩიეთ ფაილი (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
    
    if file and st.button("ამოცნობა და ძიება 🚀"):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            vin_code = extract_vin(file.getvalue())
            if vin_code:
                st.session_state.vin = vin_code
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ ამოიცნო.")
                
    st.divider()
    manual_vin = st.text_input("ან შეიყვანეთ VIN ხელით:")
    if manual_vin and st.button("ხელით ძიება 🔍"):
        st.session_state.vin = manual_vin.upper().strip()
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header(f"ნაპოვნია VIN: {st.session_state.vin}")
    
    google_url = f"https://www.google.com/search?q={st.session_state.vin}"
    
    st.info("დააჭირეთ ღილაკს ინფორმაციის სანახავად:")
    st.link_button("🌐 მოძებნე Google-ში", google_url, use_container_width=True)
    
    st.divider()
    
    if st.button("🔄 სხვა მანქანის შემოწმება"):
        st.session_state.step = 1
        st.session_state.vin = None
        st.rerun()
