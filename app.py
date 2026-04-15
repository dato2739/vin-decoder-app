import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
import re

# Page configuration
st.set_page_config(page_title="VIN Scanner AI", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { color: #1e3a8a; text-align: center; font-size: 2rem; font-weight: bold; margin-bottom: 20px; }
    .result-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_index=True)

st.markdown('<div class="main-title">VIN კოდის AI სკანერი</div>', unsafe_allow_index=True)

@st.cache_resource
def load_reader():
    # Load English model for OCR
    return easyocr.Reader(['en'])

reader = load_reader()

def preprocess_image(image):
    # Image processing for better accuracy
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    return enhanced

def extract_vin(image_np):
    # Detect text
    results = reader.readtext(image_np)
    # Standard VIN pattern (17 chars, no I, O, Q)
    vin_pattern = re.compile(r'[A-HJ-NPR-Z0-9]{17}')
    
    all_text = ""
    for (bbox, text, prob) in results:
        # Clean text: remove spaces, convert to upper, fix common OCR mistakes
        clean_text = re.sub(r'\s+', '', text).upper().replace('I', '1').replace('O', '0').replace('Q', '0')
        all_text += clean_text
        
    match = vin_pattern.search(all_text)
    if match:
        return match.group(0)
    
    # Secondary check: find any 17-char alphanumeric string
    for (bbox, text, prob) in results:
        clean = re.sub(r'[^A-Z0-9]', '', text.upper())
        if len(clean) == 17:
            return clean
    return None

uploaded_file = st.file_uploader("გადაუღეთ ფოტო VIN კოდს ან ატვირთეთ", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="ატვირთული ფოტო", use_container_width=True)
    
    with st.spinner('AI აანალიზებს კოდს...'):
        processed_img = preprocess_image(image)
        vin = extract_vin(processed_img)
        
        if vin:
            st.markdown(f"""
            <div class="result-box">
                <p style="margin:0; color: #6b7280; font-size: 0.9rem;">ამოცნობილი VIN კოდი:</p>
                <h2 style="margin:0; color: #065f46; letter-spacing: 2px;">{vin}</h2>
            </div>
            """, unsafe_allow_index=True)
            st.balloons()
        else:
            st.error("ვერ მოხერხდა კოდის წაკითხვა. გთხოვთ, გადაიღოთ უფრო ახლოდან და მკაფიოდ.")

st.divider()
st.info("რჩევა: საუკეთესო შედეგისთვის, კამერა გეჭიროთ VIN კოდის პარალელურად და მოერიდეთ შუქის არეკვლას.")
