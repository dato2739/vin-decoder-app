import streamlit as st
import requests
import base64
import re
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="VIN AI Pro - v1.4", page_icon="🚗", layout="wide")

# --- კონფიგურაცია ---
API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs" # Google Vision
CRAWLBASE_TOKEN = "TK60Uv1w-M8YVf-6U9J0Fw" # Crawlbase (Javascript Token)

# --- ფუნქციები ---
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
        for block in processed_text.split():
            clean_block = re.sub(r'[^A-Z0-9]', '', block)
            if len(clean_block) == 17 and is_valid_vin(clean_block):
                return clean_block
    return None

def get_auction_images_from_bid_cars(vin):
    """
    Crawlbase-ის მეშვეობით bid.cars-იდან სურათების ბმულების ამოღება
    """
    if not CRAWLBASE_TOKEN or CRAWLBASE_TOKEN == "YOUR_CRAWLBASE_JS_TOKEN":
        return [], "Crawlbase API Token არ არის მითითებული."

    # 1. Google Search site:bid.cars VIN (მკაცრი ძებნა კონკრეტულ ლოტზე)
    search_query = f"site:bid.cars \"{vin}\""
    google_search_url = f"https://www.google.com/search?q={search_query}"
    
    # 2. ვიყენებთ Crawlbase-ს Google Search-ის წასაკითხად
    crawlbase_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={requests.utils.quote(google_search_url)}"
    
    image_links = []
    error_message = None

    try:
        response = requests.get(crawlbase_url, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # ვეძებთ bid.cars-ის პირველ ლინკს შედეგებში
            target_link = None
            for a in soup.find_all('a', href=True):
                if "bid.cars/en/lot/" in a['href']:
                    target_link = a['href']
                    break
            
            if target_link:
                # 3. კვლავ ვიყენებთ Crawlbase-ს, რომ წავიკითხოთ თავად bid.cars ლოტის გვერდი
                target_crawl_url = f"https://api.crawlbase.com/?token={CRAWLBASE_TOKEN}&url={requests.utils.quote(target_link)}"
                lot_response = requests.get(target_crawl_url, timeout=15)
                
                if lot_response.status_code == 200:
                    lot_soup = BeautifulSoup(lot_response.text, 'html.parser')
                    # bid.cars-ის HTML სტრუქტურა სურათებისთვის (ამ ეტაპზე)
                    # ვეძებთ <img> ტეგებს, რომლებსაც აქვთ bid.cars-ის სურათების ბმულები
                    for img in lot_soup.find_all('img', src=True):
                        src = img['src']
                        if "bidcars-live.b-cdn.net" in src and "/photos/" in src:
                            # bid.cars ხშირად იყენებს "thumbnail" სურათებს.
                            # ვცდილობთ Thumbnail-ის სრულ სურათად გადაკეთებას (თუ შესაძლებელია)
                            full_src = src.replace("-thumbnail", "") 
                            if full_src not in image_links:
                                image_links.append(full_src)
                                
                    if not image_links:
                        error_message = "სურათები bid.cars-ის გვერდზე ვერ მოიძებნა."
                else:
                    error_message = f"bid.cars-ის გვერდის წაკითხვა ვერ მოხერხდა (Status: {lot_response.status_code})."
            else:
                error_message = f"bid.cars-ზე ამ VIN-ის შესაბამისი ლოტი Google-ში ვერ მოიძებნა (ძებნა: {search_query})."
        else:
            error_message = f"Google-ში ძებნა ვერ მოხერხდა (Crawlbase Status: {response.status_code})."
    except requests.exceptions.Timeout:
        error_message = "მოთხოვნის დრო ამოიწურა. სცადეთ მოგვიანებით."
    except Exception as e:
        error_message = f"მოხდა გაუთვალისწინებელი შეცდომა: {str(e)}"
        
    return image_links, error_message

# --- სესიის მართვა ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

def go_home():
    st.session_state['page'] = 'home'
    st.session_state['auction_images'] = []
    st.session_state['scraping_error'] = None

# --- მთავარი გვერდი ---
if st.session_state['page'] == 'home':
    st.title("🚗 VIN AI Pro - v1.4 (Auto Scraper)")
    uploaded_file = st.file_uploader("ატვირთეთ VIN სტიკერი", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        st.image(uploaded_file, width=400)
        if st.button("დეტალური ანალიზის დაწყება (Scraping)", use_container_width=True):
            vin = scan_vin_strict(uploaded_file.getvalue())
            if vin:
                st.session_state['active_vin'] = vin
                # ვიწყებთ სურათების Scraping-ს
                with st.spinner("მიმდინარეობს აუქციონის სურათების წამოღება (bid.cars)..."):
                    images, error = get_auction_images_from_bid_cars(vin)
                    st.session_state['auction_images'] = images
                    st.session_state['scraping_error'] = error
                st.session_state['page'] = 'analysis'
                st.rerun()
            else:
                st.error("❌ VIN კოდი ვერ ამოიცნო.")

# --- ანალიზის გვერდი (ავტო-სურათებით) ---
elif st.session_state['page'] == 'analysis':
    vin = st.session_state['active_vin']
    st.button("⬅️ მთავარი გვერდი", on_click=go_home)
    st.title(f"📊 დეტალური ანგარიში (v1.4): {vin}")
    st.divider()

    # --- სურათების სექცია ---
    st.subheader("🖼️ აუქციონის სურათები (Auto Scraped from bid.cars)")
    
    if st.session_state.get('scraping_error'):
        st.error(f"⚠️ სურათების წამოღებისას მოხდა შეცდომა: {st.session_state['scraping_error']}")
        st.write("---")
        st.subheader("🔗 პირდაპირი წვდომა bid.cars-ზე (manual)")
        bid_cars_search = f"https://bid.cars/en/search/results?q={vin}"
        st.link_button("🚀 გახსენი bid.cars (სრული ინფორმაცია)", bid_cars_search, use_container_width=True, type="primary")
        
    elif st.session_state.get('auction_images'):
        images = st.session_state['auction_images']
        st.success(f"✅ ნაპოვნია {len(images)} სურათი bid.cars-ზე.")
        
        # ვაჩვენებთ სურათებს გალერეის სახით (3 სვეტად)
        cols = st.columns(3)
        for idx, img_url in enumerate(images):
            with cols[idx % 3]:
                st.image(img_url, use_container_width=True)
    else:
        st.info("სურათები bid.cars-ის გვერდზე ვერ მოიძებნა (შესაძლოა ლოტი ძველია ან არასწორად ინდექსირებული).")

    st.divider()
    
    # სხვა წყაროები
    st.write("🔍 **სხვა დამხმარე ბაზები:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("🖼️ BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={vin}", use_container_width=True)
    with c2:
        st.link_button("📜 PLC.ua ფასები", f"https://plc.ua/ca/vin-check/?vin={vin}", use_container_width=True)
    with c3:
        st.link_button("📊 Carfax", f"https://www.carfax.com/vin/{vin}", use_container_width=True)
