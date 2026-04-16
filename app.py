import streamlit as st
import requests
import base64
import json
import re
from fpdf import FPDF

# --- კონფიგურაცია ---
st.set_page_config(page_title="AI Car Investigator PRO", layout="wide", page_icon="🕵️‍♂️")

# API გასაღებები (შენი პირადი გასაღებები)
VISION_API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"
GEMINI_API_KEY = "AQ.Ab8RN6KdNUGtysSIXZJtVJG9NllSmGPfsaDinEW9Q89hl8nxDw"

# სესიის ინიციალიზაცია
if 'step' not in st.session_state: st.session_state.step = 1
if 'vin' not in st.session_state: st.session_state.vin = None
if 'sc_data' not in st.session_state: st.session_state.sc_data = []

# --- დამხმარე ფუნქციები ---

def scan_vin(image_bytes):
    """Google Vision API VIN-ის ამოსაცნობად"""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"
    payload = {"requests": [{"image": {"content": encoded}, "features": [{"type": "TEXT_DETECTION"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        text = res['responses'][0]['textAnnotations'][0]['description']
        # ეძებს 17-ნიშნა VIN კოდს
        match = re.search(r'[A-Z0-9]{17}', text.upper().replace('O', '0'))
        return match.group(0) if match else None
    except: return None

def analyze_with_gemini(images):
    """Gemini 1.5 Flash სურათების ანალიზისთვის"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    image_parts = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img.getvalue()).decode('utf-8')}} for img in images]

    # ინსტრუქცია AI-სთვის
    prompt_text = """
    Analyze these car auction screenshots and photos.
    1. Extract technical data: VIN, Final Price (with $), Odometer (mileage), Sale Document status.
    2. In Georgian, describe visual damage analysis. Identify specific zones (hood, lights, bumper).
    3. Final verdict in Georgian: Worth buying?
    Return ONLY a valid JSON object:
    {"vin": "", "price": "", "mileage": "", "doc": "", "analysis_ka": "", "verdict_ka": ""}
    """

    payload = {"contents": [{"parts": [*image_parts, {"text": prompt_text}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        # 'candidates' ერორის პრევენცია
        if 'candidates' in result and result['candidates']:
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            return json.loads(json_match.group(0))
        else:
            return {"error": "AI-მ პასუხი ვერ დააბრუნა. სცადეთ სხვა ფოტოები."}
    except Exception as e:
        return {"error": str(e)}

def generate_pdf(report):
    """PDF-ის გენერირება შეცდომების გარეშე"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Vehicle Investigation Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=12)
    
    # მონაცემების ჩაწერა (მხოლოდ ლათინური PDF-სთვის)
    pdf.multi_cell(0, 10, f"VIN: {report.get('vin', 'N/A')}")
    pdf.multi_cell(0, 10, f"Price: {report.get('price', 'N/A')}")
    pdf.multi_cell(0, 10, f"Mileage: {report.get('mileage', 'N/A')}")
    pdf.multi_cell(0, 10, f"Document: {report.get('doc', 'N/A')}")
    
    return pdf.output()

# --- ინტერფეისი ---

if st.session_state.step == 1:
    st.title("📸 ნაბიჯი 1: VIN-ის დაფიქსირება")
    source = st.file_uploader("ატვირთეთ მანქანის VIN ფოტო", type=['jpg', 'jpeg', 'png'])
    if not source:
        cam = st.camera_input("ან გადაუღეთ პირდაპირ")
        source = cam

    if source and st.button("გაგრძელება ➡️"):
        with st.spinner("მიმდინარეობს VIN კოდის ამოცნობა..."):
            vin_res = scan_vin(source.getvalue())
            if vin_res:
                st.session_state.vin = vin_res
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("VIN კოდი ვერ მოიძებნა. სცადეთ უკეთესი ხარისხის ფოტო.")

elif st.session_state.step == 2:
    st.title(f"🚀 სამუშაო სივრცე: {st.session_state.vin}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌐 მოიძიეთ ინფორმაცია")
        # BidFax-ის ლინკი, რომელიც ახალ ფანჯარაში იხსნება
        st.link_button("📊 გახსენი BidFax ისტორია", f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}")
        st.link_button("🚘 გახსენი Bid.cars ძებნა", f"https://bid.cars/en/search/results?q={st.session_state.vin}")
        st.info("მოაგროვეთ სქრინშოტები და ატვირთეთ მარჯვენა პანელში.")

    with col2:
        st.subheader("📤 ატვირთეთ სქრინშოტები")
        scs = st.file_uploader("ამოირჩიეთ აუქციონის ფოტოები", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
        
        if scs:
            st.session_state.sc_data = scs
            if st.button("🔥 სრული AI ანალიზი"):
                st.session_state.step = 3
                st.rerun()

elif st.session_state.step == 3:
    st.title("🧠 AI ექსპერტიზის შედეგი")
    
    with st.spinner("AI ამუშავებს მონაცემებს..."):
        report = analyze_with_gemini(st.session_state.sc_data)
        
        if "error" not in report:
            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                st.metric("ბოლო ფასი", report.get('price', '$0'))
                st.metric("გარბენი", report.get('mileage', 'N/A'))
                st.write(f"**დოკუმენტი:** {report.get('doc', 'N/A')}")
            
            with c2:
                st.markdown("### 📝 ვიზუალური ანალიზი")
                st.write(report.get('analysis_ka', 'ინფორმაცია ვერ მოიძებნა.'))
                st.divider()
                st.warning(f"💡 **ვერდიქტი:** {report.get('verdict_ka', 'N/A')}")
            
            st.divider()
            
            # PDF-ის ჩამოტვირთვა
            pdf_bytes = generate_pdf(report)
            st.download_button(
                label="📄 ჩამოტვირთე PDF რეპორტი (EN)",
                data=bytes(pdf_bytes),
                file_name=f"Report_{st.session_state.vin}.pdf",
                mime="application/pdf"
            )
        else:
            st.error(f"შეცდომა: {report['error']}")

    if st.button("🔄 თავიდან დაწყება"):
        st.session_state.step = 1
        st.session_state.sc_data = []
        st.rerun()
