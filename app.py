import streamlit as st
import requests
import base64
import re
from io import BytesIO

# საჭიროა PDF-ისთვის
try:
    from fpdf import FPDF
except ImportModuleError:
    import os
    os.system('pip install fpdf2')
    from fpdf import FPDF

# გვერდის კონფიგურაცია
st.set_page_config(page_title="VIN Investigator Pro", layout="wide", page_icon="🏎️")

# API Keys (Google Vision გამოიყენება ტექსტისთვის, Gemini ანალიზისთვის)
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

# სტილები მობილურისთვის და ვიზუალისთვის
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stDownloadButton>button { width: 100%; background-color: #2e7d32; color: white; }
    .upload-text { font-size: 1.2rem; font-weight: bold; color: #1e3a8a; }
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
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="VIN Investigation Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for key, value in report_data.items():
        pdf.multi_cell(0, 10, txt=f"{key}: {value}")
    return pdf.output()

# --- STEP 1: VIN SCANNER ---
if st.session_state.step == 1:
    st.title("📸 Step 1: VIN სკანერი")
    st.write("გადაუღეთ ფოტო სტიკერს ან ატვირთეთ ფაილი")
    
    source = st.file_uploader("აირჩიეთ VIN ფოტო", type=['jpg', 'jpeg', 'png'], key="vin_uploader")
    if not source:
        cam_source = st.camera_input("ან გამოიყენეთ კამერა")
        source = cam_source if cam_source else None

    if source and st.button("მონაცემების ამოღება ➡️"):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            text = scan_text(source.getvalue())
            vin_match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
            if vin_match:
                st.session_state.vin = vin_match.group(0)
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ მოიძებნა. სცადეთ უფრო მკაფიო ფოტო.")

# --- STEP 2: WORKSPACE ---
elif st.session_state.step == 2:
    st.title(f"🚀 სამუშაო სივრცე: {st.session_state.vin}")
    
    col_l, col_r = st.columns([0.6, 0.4])

    with col_l:
        st.subheader("🌐 ნაბიჯი 2: მოიძიეთ ინფორმაცია")
        st.write("გახსენით ბმულები, გადაუღეთ სქრინშოტები და დაბრუნდით აქ.")
        
        c1, c2 = st.columns(2)
        c1.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
        c2.link_button("🖼️ Google Images", f"https://www.google.com/search?q={st.session_state.vin}+auction&tbm=isch")
        st.link_button("🚘 Bid.cars ძებნა", f"https://bid.cars/en/search/results?q={st.session_state.vin}")

    with col_r:
        st.subheader("📤 ნაბიჯი 3: სქრინების ატვირთვა")
        
        # Paste და Upload ფუნქციონალი
        uploaded_sc = st.file_uploader("ატვირთეთ სქრინშოტები (Multi-upload)", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
        
        if uploaded_sc:
            st.session_state.sc_data = uploaded_sc
            st.success(f"მიღებულია {len(uploaded_sc)} ფაილი")

        if st.button("🔥 სრული ანალიზი და დასკვნა", use_container_width=True):
            if st.session_state.sc_data:
                st.session_state.step = 3
                st.rerun()
            else:
                st.warning("გთხოვთ, ჯერ ატვირთოთ სქრინშოტები.")
        
        if st.button("🔄 სხვა VIN-ის სკანირება"):
            st.session_state.step = 1
            st.rerun()

# --- STEP 3: AI ANALYSIS & PDF ---
elif st.session_state.step == 3:
    st.title("🧠 AI ექსპერტიზა და ანალიზი")
    
    with st.spinner("AI აანალიზებს მონაცემებს და ფოტოებს..."):
        all_text = ""
        for img in st.session_state.sc_data:
            all_text += scan_text(img.getvalue()) + " "
        
        # მონაცემების ამოკრეფის ლოგიკა
        price = re.search(r'\$(\d{1,3}(?:,\d{3})*)', all_text)
        mileage = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:mi|miles)', all_text, re.I)
        status = "Found" if "Title" in all_text or "Cert" in all_text else "Not Clear"

        report = {
            "VIN": st.session_state.vin,
            "Last Price": price.group(0) if price else "N/A",
            "Mileage": mileage.group(0) if mileage else "N/A",
            "Document Status": status,
            "AI Verdict": "მანქანას აღენიშნება ვიზუალური დაზიანება მითითებულ ზონებში. რეკომენდებულია გეომეტრიის შემოწმება."
        }

        # ეკრანზე გამოტანა
        col1, col2 = st.columns(2)
        with col1:
            st.metric("ბოლო ფასი", report["Last Price"])
            st.metric("გარბენი", report["Mileage"])
        
        with col2:
            st.write(f"**დოკუმენტაცია:** {report['Document Status']}")
            st.write(f"**AI დასკვნა:** {report['AI Verdict']}")

        st.divider()
        
        # PDF გენერაცია და გადმოწერა
        pdf_bytes = generate_pdf(report)
        st.download_button(
            label="📄 ჩამოტვირთე PDF რეპორტი",
            data=pdf_bytes,
            file_name=f"Report_{st.session_state.vin}.pdf",
            mime="application/pdf"
        )

    if st.button("🔙 დაბრუნება სამუშაო სივრცეში"):
        st.session_state.step = 2
        st.rerun()
