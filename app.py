import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI Linker", page_icon="📸")

# Google Vision API Key
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def scan_vin(image_bytes):
    """Google Vision-ით ტექსტის ამოკითხვა"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        if 'responses' in res and res['responses'][0].get('textAnnotations'):
            text = res['responses'][0]['textAnnotations'][0]['description']
            # VIN კოდის ძებნა ტექსტში
            for block in text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17: return clean
    except: pass
    return None

st.title("📸 VIN Scanner & Linker")
st.write("გადაუღეთ ფოტო მანქანის VIN სტიკერს")

# label_visibility="collapsed" ვიზუალურად უფრო სუფთაა მობილურისთვის
uploaded_file = st.file_uploader(
    "აირჩიეთ ფოტო ან გადაუღეთ კამერით", 
    type=['jpg', 'jpeg', 'png'],
    help="მობილურზე დაჭერისას ამოირჩიეთ 'Camera'"
)

if uploaded_file:
    # ვაჩვენებთ ფოტოს, რომ მომხმარებელმა ნახოს, ხარისხიანია თუ არა
    st.image(uploaded_file, caption="სკანირებული ფოტო", use_container_width=True)
    
    if st.button("🔎 ინფორმაციის მოძიება", use_container_width=True):
        with st.spinner("მიმდინარეობს VIN კოდის ამოცნობა..."):
            vin = scan_vin(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ ნაპოვნია VIN: {vin}")
                st.divider()
                
                # დიდი ღილაკები თითით მარტივად დასაჭერად
                st.markdown("### 🔗 სწრაფი ბმულები:")
                
                st.link_button(
                    "🌐 ნახე Google Images (ფოტოები)", 
                    f"https://www.google.com/search?q={vin}+auction&tbm=isch",
                    use_container_width=True
                )
                
                st.link_button(
                    "📊 ნახე BidFax (ისტორია)", 
                    f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}",
                    use_container_width=True
                )
                
                st.link_button(
                    "🚗 ნახე Bid.cars", 
                    f"https://bid.cars/en/search/results?q={vin}",
                    use_container_width=True
                )
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო. დარწმუნდით, რომ ფოტოზე კოდი მკაფიოდ ჩანს.")
