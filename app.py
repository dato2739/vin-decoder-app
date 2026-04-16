import streamlit as st
import requests
import base64
import re

st.set_page_config(page_title="VIN AI - Auction Analyzer", page_icon="🚗", layout="centered")

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# დაზიანების ლექსიკონი ანალიზისთვის
DAMAGE_MAP = {
    "front end": "წინა მხარის დაზიანება (ბამპერი, რადიატორი, ძრავის საფარი)",
    "rear end": "უკანა მხარის დაზიანება (საბარგული, ბამპერი)",
    "side": "გვერდითი დარტყმა (კარები, ცენტრალური სტოიკა)",
    "all over": "მთლიანი კორპუსის დაზიანება (შესაძლოა გადატრიალებული)",
    "water/flood": "წყალში ნამყოფი (საშიშია ელექტროობისთვის!)",
    "burn": "ნაწვარი (ხშირად აღდგენას არ ექვემდებარება)",
    "biohazard": "ბიოლოგიური საფრთხე (სალონში სისხლი, ობი ან სხვა)",
    "mechanical": "ძრავის ან გადაცემათა კოლოფის პრობლემა",
    "minor dents": "მცირე ნაჭდევები/ჩაზნექილობა",
    "normal wear": "ბუნებრივი ცვეთა",
    "frame damage": "ჩონჩხის/რამის დაზიანება (სერიოზული საფრთხე!)"
}

def analyze_auction_text(text):
    text = text.lower()
    found_issues = []
    
    for key, val in DAMAGE_MAP.items():
        if key in text:
            found_issues.append(val)
            
    if "run and drive" in text:
        status = "✅ მანქანა იქოქება და დადის (Run & Drive)"
    elif "starts" in text:
        status = "⚠️ მანქანა იქოქება, მაგრამ არ დადის"
    else:
        status = "❌ არ იქოქება / სტატუსი უცნობია"
        
    return found_issues, status

# --- ძირითადი ფუნქციები (VIN სკანირება) ---
def is_valid_vin(vin):
    return bool(re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin))

def scan_vin_strict(image_bytes):
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {"requests": [{"image": {"content": encoded_image}, "features": [{"type": "TEXT_DETECTION"}]}]}
    response = requests.post(url, json=payload)
    result = response.json()
    if 'responses' in result and result['responses'][0].get('textAnnotations'):
        full_text = result['responses'][0]['textAnnotations'][0]['description']
        processed_text = full_text.upper().replace('O', '0')
        potential_blocks = processed_text.split()
        for block in potential_blocks:
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            if len(clean_block) == 17 and is_valid_vin(clean_block):
                return clean_block
    return None

# --- ინტერფეისი ---
st.title("🚗 VIN & Auction Smart Analyzer")

tabs = st.tabs(["VIN სკანერი", "აუქციონის ტექსტური ანალიზი"])

with tabs[0]:
    uploaded_file = st.file_uploader("ატვირთეთ VIN სტიკერი", type=['jpg', 'jpeg', 'png'])
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
        if st.button("VIN-ის ამოცნობა"):
            vin = scan_vin_strict(uploaded_file.getvalue())
            if vin:
                st.success(f"ამოცნობილია: {vin}")
                st.code(vin)
                st.link_button("Google ძებნა", f"https://www.google.com/search?q={vin}+auction+damage")
            else:
                st.error("VIN ვერ მოიძებნა")

with tabs[1]:
    st.subheader("აუქციონის აღწერილობის გაშიფვრა")
    auction_text = st.text_area("ჩააკოპირეთ ტექსტი აუქციონის გვერდიდან (მაგ: Primary Damage: Front End...)", height=150)
    
    if st.button("ანალიზი"):
        if auction_text:
            issues, drive_status = analyze_auction_text(auction_text)
            
            st.write("### 📊 შედეგები:")
            st.info(drive_status)
            
            if issues:
                st.warning("ნაპოვნია დაზიანებები:")
                for issue in issues:
                    st.write(f"- {issue}")
            else:
                st.success("ტექსტში კრიტიკული დაზიანებები არ იკვეთება.")
        else:
            st.error("გთხოვთ, შეიყვანოთ ტექსტი.")
