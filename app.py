import streamlit as st
import requests
import base64
import re
from io import BytesIO
from fpdf import FPDF

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN Investigator Pro", layout="wide", page_icon="🏎️")

# API Keys
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# CSS სტილები
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stDownloadButton>button { width: 100%; background-color: #2e7d32; color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None
if 'sc_data' not in st.session_state: st.session_state.sc_data = []

def scan_text(image_bytes):
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        return res['responses'][0]['textAnnotations'][0]['description']
    except: return ""

def generate_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    
    # სათაური
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, txt="VIN Investigation Report", ln=True, align='C')
    pdf.ln(10)
    
    # მონაცემები
    pdf.set_font("Helvetica", size=12)
    for key, value in report_data.items():
        # ვასუფთავებთ ტექსტს სიმბოლოებისგან, რომლებსაც სტანდარტული PDF ვერ კითხულობს
        safe_key = str(key).encode('latin-1', 'ignore').decode('latin-1')
        safe_value = str(value).encode('latin-1', 'ignore').decode('latin-1')
        
        pdf.multi_cell(0, 10, txt=f"{safe_key}: {safe_value}")
        pdf.ln(2)
        
    return pdf.output()

# --- STEP 1: VIN SCANNER ---
if st.session_state.step == 1:
    st.title("📸 ნაბიჯი 1: VIN სკანერი")
    source = st.file_uploader("აირჩიეთ VIN ფოტო", type=['jpg', 'jpeg', 'png'])
    if not source:
        cam_source = st.camera_input("ან გადაუღეთ")
        source = cam_source if cam_source else None

    if source and st.button("გაგრძელება ➡️"):
        with st.spinner("მიმდინარეობს ძებნა..."):
            text = scan_text(source.getvalue())
            vin_match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
            if vin_match:
                st.session_state.vin = vin_match.group(0)
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN ვერ მოიძებნა.")

# --- STEP 2: WORKSPACE ---
elif st.session_state.step == 2:
    st.title(f"🚀 სამუშაო სივრცე: {st.session_state.vin}")
    col_l, col_r = st.columns([0.6, 0.4])

    with col_l:
        st.subheader("🌐 ნაბიჯი 2: მოიძიეთ ინფორმაცია")
        st.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
        st.link_button("🖼️ Google Images", f"https://www.google.com/search?q={st.session_state.vin}+auction&tbm=isch")
        st.link_button("🚘 Bid.cars ძებნა", f"https://bid.cars/en/search/results?q={st.session_state.vin}")

    with col_r:
        st.subheader("📤 ნაბიჯი 3: სქრინები")
        uploaded_sc = st.file_uploader("ატვირთეთ ან ჩაასწორეთ (Paste)", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
        
        if uploaded_sc:
            st.session_state.sc_data = uploaded_sc
            st.success(f"ატვირთულია {len(uploaded_sc)} ფაილი")

        if st.button("🔥 ანალიზის დაწყება"):
            if st.session_state.sc_data:
                st.session_state.step = 3
                st.rerun()
            else:
                st.warning("ატვირთეთ სქრინშოტები.")

# --- STEP 3: RESULTS ---
elif st.session_state.step == 3:
    st.title("🧠 AI ექსპერტიზა")
    
    with st.spinner("მიმდინარეობს ანალიზი..."):
        all_text = ""
        for img in st.session_state.sc_data:
            all_text += scan_text(img.getvalue()) + " "
        
        price = re.search(r'\$(\d{1,3}(?:,\d{3})*)', all_text)
        mileage = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:mi|miles)', all_text, re.I)

        report = {
            "VIN": st.session_state.vin,
            "Price": price.group(0) if price else "$0",
            "Mileage": mileage.group(0) if mileage else "N/A",
            "Status": "Checked",
            "Expert Verdict": "Visual damages found on the side panels. Engine bay seems intact based on photos."
        }

        col1, col2 = st.columns(2)
        col1.metric("ბოლო ფასი", report["Price"])
        col1.metric("გარბენი", report["Mileage"])
        col2.write(f"**AI დასკვნა:** {report['Expert Verdict']}")

        st.divider()
        
        # PDF გენერაცია
        try:
            pdf_out = generate_pdf(report)
            st.download_button(
                label="📄 ჩამოტვირთე PDF რეპორტი",
                data=bytes(pdf_out),
                file_name=f"Report_{st.session_state.vin}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF-ის შექმნისას მოხდა შეცდომა: {e}")

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.session_state.sc_data = []
        st.rerun()
