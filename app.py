import streamlit as st
import requests
import base64
import re

# გვერდის კონფიგურაცია მობილურისთვის
st.set_page_config(page_title="VIN Scanner Pro", page_icon="📸", layout="centered")

# Google Vision API გასაღები
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def scan_vin(image_bytes):
    """Google Vision-ით VIN კოდის ამოცნობა ფოტოდან"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {
        "requests": [{
            "image": {"content": encoded},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        if 'responses' in res and res['responses'][0].get('textAnnotations'):
            text = res['responses'][0]['textAnnotations'][0]['description']
            # ვეძებთ 17 სიმბოლიან VIN ფორმატს
            for block in text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17:
                    return clean
    except Exception as e:
        st.error(f"API შეცდომა: {e}")
    return None

# ინტერფეისი
st.title("🚗 VIN AI სკანერი")
st.write("გადაუღეთ ფოტო სტიკერს ან ატვირთეთ ფაილი")

# მეთოდის არჩევა
mode = st.radio("აირჩიეთ წყარო:", ["📷 კამერა (Live)", "📁 გალერეა/ფაილი"], horizontal=True)

captured_image = None

if mode == "📷 კამერა (Live)":
    # პირდაპირ ხსნის კამერას ეკრანზე
    captured_image = st.camera_input("გაასწორეთ VIN კოდი კადრში")
else:
    # ფაილის ატვირთვის სტანდარტული ღილაკი
    captured_image = st.file_uploader("ამოირჩიეთ ფოტო", type=['jpg', 'jpeg', 'png'])

if captured_image:
    if st.button("🔎 მონაცემების მოძიება", use_container_width=True):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            vin_code = scan_vin(captured_image.getvalue())
            
            if vin_code:
                st.success(f"✅ ამოცნობილია: {vin_code}")
                st.divider()
                
                st.subheader("🔗 სწრაფი ბმულები")
                
                # Google Images - საუკეთესოა ფოტოების სწრაფად სანახავად
                st.link_button(
                    "🖼️ ნახე ფოტოები (Google Images)", 
                    f"https://www.google.com/search?q={vin_code}+auction&tbm=isch",
                    use_container_width=True
                )
                
                # BidFax - აუქციონის ისტორიისთვის
                st.link_button(
                    "📊 ნახე ისტორია (BidFax)", 
                    f"https://bidfax.info/index.php?do=search&subaction=search&story={vin_code}",
                    use_container_width=True
                )
                
                # Bid.cars - ალტერნატიული წყარო
                st.link_button(
                    "🚘 ნახე Bid.cars-ზე", 
                    f"https://bid.cars/en/search/results?q={vin_code}",
                    use_container_width=True
                )
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო. სცადეთ უფრო მკაფიო ფოტო ან სხვა კუთხე.")

st.info("შენიშვნა: კამერის გამოსაყენებლად ბრაუზერს მიეცით ნებართვა (Allow Camera).")
