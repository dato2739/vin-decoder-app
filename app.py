import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
import re

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN Scanner AI", page_icon="🔍")

st.title("🚗 VIN კოდის AI სკანერი")
st.write("ატვირთეთ ფოტო 17-ნიშნა კოდის ამოსაცნობად")

@st.cache_resource
def load_reader():
    # ჩატვირთვა
    return easyocr.Reader(['en'])

reader = load_reader()

def extract_vin(image):
    img_np = np.array(image)
    results = reader.readtext(img_np)
    
    # VIN-ის ძებნა (17 სიმბოლო, I, O, Q-ს გარეშე)
    vin_pattern = re.compile(r'[A-HJ-NPR-Z0-9]{17}')
    
    combined_text = ""
    for (bbox, text, prob) in results:
        clean = re.sub(r'\s+', '', text).upper().replace('I', '1').replace('O', '0').replace('Q', '0')
        combined_text += clean
        
    match = vin_pattern.search(combined_text)
    if match:
        return match.group(0)
    return None

uploaded_file = st.file_uploader("აირჩიეთ სურათი", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="ატვირთული ფოტო", use_container_width=True)
    
    with st.spinner('მიმდინარეობს ანალიზი...'):
        vin_result = extract_vin(img)
        
        if vin_result:
            st.success("✅ კოდი ნაპოვნია:")
            st.subheader(vin_result)
        else:
            st.error("ვერ მოხერხდა 17-ნიშნა კოდის ამოცნობა. სცადეთ უფრო ახლოდან გადაღება.")

st.info("საუკეთესო შედეგისთვის, გადაიღეთ კოდი მკაფიოდ, პირდაპირი კუთხით.")
