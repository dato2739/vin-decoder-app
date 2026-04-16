import streamlit as st
import requests
import base64
import json
import re
from fpdf import FPDF

# --- კონფიგურაცია ---
st.set_page_config(page_title="AI Car Investigator PRO", layout="wide", page_icon="🕵️‍♂️")

# API გასაღებები
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

# სესიის ინიციალიზაცია
if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None
if 'sc_data' not in st.session_state: st.session_state.sc_data = []

# --- ფუნქციები ---

def scan_vin(image_bytes):
    """Google Vision API ტექსტის და VIN-ის ამოსაცნობად"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload).json()
        text = res['responses'][0]['textAnnotations'][0]['description']
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except: return None

def analyze_with_gemini(images):
    """Gemini 1.5 Flash სურათების ვიზუალური ანალიზისთვის"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    image_parts = []
    for img in images:
        image_parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img.getvalue()).decode('utf-8')
            }
        })

    prompt_text = """
    Analyze these car auction images. 
    1. Extract technical data: VIN, Final Price (with $), Odometer (mileage), Sale Document status.
    2. Provide a detailed visual damage analysis in Georgian. Describe specific areas (hood, bumper, etc.) and potential hidden risks.
    3. Final verdict in Georgian: Is it a good buy?
    Return ONLY a JSON object: 
    {"vin": "", "price": "", "mileage": "", "doc": "", "analysis_ka": "", "verdict_ka": ""}
    """

    payload = {"contents": [{"parts": [*image_parts, {"text": prompt_text}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        raw_text = result['candidates'][0]['content']['parts'][0]['text']
        # JSON-ის ამოღება ტექსტიდან
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        return json.loads(json_match.group(0))
    except Exception as e:
        return {"error": str(e)}

def generate_pdf(report):
    """PDF-ის გენერირება (უსაფრთხო ფორმატით)"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Vehicle AI Investigation Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=12)
    
    # მონაცემების ჩაწერა (მხოლოდ ლათინური სიმბოლოები PDF-სთვის)
    pdf.cell(0, 10, f"VIN: {report.get('vin', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Price: {report.get('price', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Mileage: {report.get('mileage', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Document: {report.get('doc', 'N/A')}", ln=True)
    pdf.ln(5)
    
    return pdf.output()

# --- ინტერფეისი ---

# STEP 1: VIN SCANNER
if st.session_state.step == 1:
    st.title("📸 ნაბიჯი 1: VIN სკანერი")
    source = st.file_uploader("ატვირთეთ VIN-ის ფოტო", type=['jpg', 'jpeg', 'png'])
    if not source:
        cam = st.camera_input("ან გადაუღეთ")
        source = cam if cam else None

    if source and st.button("გაგრძელება ➡️"):
        with st.spinner("მიმდინარეობს VIN-ის ამოცნობა..."):
            vin_code = scan_vin(source.getvalue())
            if vin_code:
                st.session_state.vin = vin_code
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ მოიძებნა. სცადეთ სხვა ფოტო.")

# STEP 2: AUCTION SEARCH & UPLOAD
elif st.session_state.step == 2:
    st.title(f"🚀 სამუშაო სივრცე: {st.session_state.vin}")
    
    col_links, col_upload = st.columns([0.5, 0.5])
    
    with col_links:
        st.subheader("🌐 მოიძიეთ აუქციონი")
        st.link_button("📊 BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
        st.link_button("🚘 Bid.cars ძებნა", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
        st.info("გააკეთეთ სქრინშოტები და დაბრუნდით აქ ასატვირთად.")

    with col_upload:
        st.subheader("📤 ატვირთეთ სქრინშოტები")
        files = st.file_uploader("აირჩიეთ ფაილები (1-6 ფოტო)", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
        
        if files:
            st.session_state.sc_data = files
            if st.button("🔥 სრული AI ექსპერტიზა"):
                st.session_state.step = 3
                st.rerun()

# STEP 3: AI ANALYSIS RESULT
elif st.session_state.step == 3:
    st.title("🧠 AI ექსპერტიზის შედეგი")
    
    with st.spinner("ხელოვნური ინტელექტი აანალიზებს ფოტოებს..."):
        report = analyze_with_gemini(st.session_state.sc_data)
        
        if "error" not in report:
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.metric("ბოლო ფასი", report['price'])
                st.metric("გარბენი", report['mileage'])
                st.write(f"**დოკუმენტი:** {report['doc']}")
            
            with col_res2:
                st.subheader("📝 ვიზუალური ანალიზი")
                st.write(report['analysis_ka'])
                st.divider()
                st.warning(f"💡 **ვერდიქტი:** {report['verdict_ka']}")
            
            st.divider()
            
            # PDF ჩამოტვირთვა
            pdf_data = generate_pdf(report)
            st.download_button(
                label="📄 ჩამოტვირთე PDF რეპორტი (EN)",
                data=bytes(pdf_data),
                file_name=f"Report_{st.session_state.vin}.pdf",
                mime="application/pdf"
            )
        else:
            st.error(f"ანალიზი ვერ მოხერხდა: {report['error']}")

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.session_state.sc_data = []
        st.rerun()
