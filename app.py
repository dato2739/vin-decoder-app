import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN Linker", page_icon="🔗")

# API Key Google Vision-ისთვის
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

def scan_vin(image_bytes):
    """ფოტოდან VIN კოდის ამოკითხვა"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        if 'responses' in res and res['responses'][0].get('textAnnotations'):
            text = res['responses'][0]['textAnnotations'][0]['description']
            # ვეძებთ 17 სიმბოლიან კოდს
            for block in text.upper().replace('O', '0').split():
                clean = re.sub(r'[^A-Z0-9]', '', block)
                if len(clean) == 17: return clean
    except: pass
    return None

st.title("🚗 VIN AI - სწრაფი ლინკები")
st.write("ატვირთეთ ფოტო და გადადით პირდაპირ აუქციონის გვერდზე")

uploaded_file = st.file_uploader("ამოირჩიეთ VIN სტიკერის ფოტო", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(uploaded_file, width=300)
    
    if st.button("ლინკების გენერირება", use_container_width=True):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            vin = scan_vin(uploaded_file.getvalue())
            
            if vin:
                st.success(f"✅ VIN კოდი: {vin}")
                st.divider()
                
                st.subheader("🔗 გადადით აუქციონის გვერდებზე:")
                
                # Google Search ლინკი (ყველაზე იმედიანი ვარიანტი)
                google_url = f"https://www.google.com/search?q={vin}+auction"
                st.link_button("🔍 მოძებნე Google-ში (სურათები/ლოტები)", google_url, use_container_width=True)
                
                # BidFax პირდაპირი ძებნა
                bidfax_url = f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}"
                st.link_button("🖼️ ნახე BidFax-ზე (ისტორია/ფოტოები)", bidfax_url, use_container_width=True)
                
                # Bid.cars პირდაპირი ძებნა
                bidcars_url = f"https://bid.cars/en/search/results?q={vin}"
                st.link_button("🚘 ნახე Bid.cars-ზე", bidcars_url, use_container_width=True)
                
                st.info("რჩევა: Google-ში გადასვლისას აირჩიეთ 'Images' განყოფილება მანქანის მდგომარეობის სწრაფად სანახავად.")
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო. სცადეთ უფრო მკაფიო ფოტო.")
