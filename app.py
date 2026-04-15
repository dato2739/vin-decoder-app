import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
import re

st.set_page_config(page_title="VIN Scanner AI", page_icon="🔍")
st.title("🚗 VIN კოდის AI სკანერი")

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])

reader = load_reader()

def enhance_image(image):
    # სურათის გაუმჯობესება OCR-სთვის
    img = np.array(image)
    # ნაცრისფერ ფერებში გადაყვანა
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # კონტრასტის ავტომატური მომატება (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    # ხმაურის მოცილება
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    return denoised

def extract_vin(image):
    processed_img = enhance_image(image)
    # ვკითხულობთ როგორც დამუშავებულ, ისე ორიგინალ სურათს მეტი სიზუსტისთვის
    results = reader.readtext(processed_img) + reader.readtext(np.array(image))
    
    # VIN-ის რეგულარული გამოსახულება
    vin_pattern = re.compile(r'[A-Z0-9]{10,17}')
    
    candidates = []
    for (bbox, text, prob) in results:
        # სიმბოლოების გასწორება (მაგ: Z -> 2, S -> 3 თუ სხვა ციფრებთანაა)
        clean = re.sub(r'\s+', '', text).upper()
        # ხშირად ერევა S და 3, Z და 2
        clean = clean.replace('I', '1').replace('O', '0').replace('Q', '0')
        
        if len(clean) >= 10:
            candidates.append(clean)
            
    # ვაერთებთ ტექსტებს თუ დანაწევრებულია
    full_text = "".join(candidates)
    matches = re.findall(r'[A-Z0-9]{17}', full_text)
    
    if matches:
        return matches[0]
    elif candidates:
        return max(candidates, key=len) # ვაბრუნებთ ყველაზე გრძელ ნაწყვეტს
    return None

uploaded_file = st.file_uploader("აირჩიეთ სურათი", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="ატვირთული ფოტო", use_container_width=True)
    
    with st.spinner('მიმდინარეობს მაღალი სიზუსტის ანალიზი...'):
        vin_result = extract_vin(img)
        
        if vin_result:
            st.success("✅ ამოცნობილი კოდი:")
            st.code(vin_result, language='text')
            if len(vin_result) != 17:
                st.warning(f"ხარვეზი: ამოცნობილია {len(vin_result)} სიმბოლო. VIN უნდა იყოს 17 ნიშნა.")
        else:
            st.error("ვერ მოხერხდა კოდის წაკითხვა.")
