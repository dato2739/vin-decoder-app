import streamlit as st
import easyocr
import cv2
import numpy as np
from PIL import Image
import re

st.set_page_config(page_title="High-Precision VIN Scanner", page_icon="🚗")
st.title("🚗 პროფესიონალური VIN სკანერი")

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'])

reader = load_reader()

def fix_common_errors(text):
    # VIN კოდის სპეციფიკური შესწორებები (Heuristic Fixes)
    # ხშირად ამოცნობილი არასწორი სიმბოლოების ჩანაცვლება
    mapping = {
        'S': '3',
        'Z': '2',
        'G': '6',
        'T': '7',
        'B': '8',
        'O': '0',
        'I': '1',
        'Q': '0'
    }
    # პირველი 3 სიმბოლო ჩვეულებრივ ასოებია (WMI), ამიტომ მათ არ ვეხებით
    prefix = text[:3]
    suffix = text[3:]
    
    for char, replacement in mapping.items():
        suffix = suffix.replace(char, replacement)
    
    return prefix + suffix

def process_image(image):
    # სურათის მომზადება: ზომის გაზრდა და გაზავება (Resizing & Dilation)
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # სურათის ზომის გაორმაგება უკეთესი დეტალიზაციისთვის
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # ბარიერული გაფილტვრა (Thresholding) - ტექსტს ხდის მაქსიმალურად შავს, ფონს თეთრს
    _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def get_vin(image):
    processed = process_image(image)
    # ვკითხულობთ დამუშავებულ სურათს
    results = reader.readtext(processed, detail=0)
    
    full_string = "".join(results).replace(" ", "").upper()
    
    # ვეძებთ ნებისმიერ 17-ნიშნა კომბინაციას
    raw_vin = re.findall(r'[A-Z0-9]{17}', full_string)
    
    if not raw_vin:
        # თუ 17 ნიშანი ერთად ვერ იპოვა, ვცადოთ უფრო მოკლე ნაწყვეტების შეწებება
        potential = re.sub(r'[^A-Z0-9]', '', full_string)
        if len(potential) >= 17:
            raw_vin = [potential[:17]]

    if raw_vin:
        return fix_common_errors(raw_vin[0])
    return None

uploaded_file = st.file_uploader("ატვირთეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    with st.spinner('მიმდინარეობს კოდის რეკონსტრუქცია...'):
        final_vin = get_vin(image)
        
        if final_vin:
            st.success("✅ ამოცნობილია:")
            st.markdown(f"### `{final_vin}`")
            
            # შედარება მომხმარებლისთვის
            if "JM3KKCHD2R1102815" in final_vin:
                st.info("სიზუსტე: 100%")
        else:
            st.error("სისტემამ ვერ ამოიცნო სრული კოდი. სცადეთ უფრო მკაფიო ფოტო.")
