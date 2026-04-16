import streamlit as st
import requests
import base64
import re

# ვაყენებთ Wide Mode-ს და ვმალავთ ზედა მენიუებს მაქსიმალური სივრცისთვის
st.set_page_config(page_title="AI Auction Tool", layout="wide", initial_sidebar_state="collapsed")

# CSS სტილი, რომ გვერდითა პანელი იყოს ძალიან ვიწრო და აუქციონმა დაიკავოს 90%
st.markdown("""
    <style>
    .stMainBlockContainer {padding-top: 1rem; padding-left: 1rem; padding-right: 1rem;}
    [data-testid="column"] { border-right: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

API_KEY = "AIzaSyAB3kFsY8BntxR-DaKmBz9CKWYsJ0QhzLs"

if 'vin' not in st.session_state: st.session_state.vin = None
if 'step' not in st.session_state: st.session_state.step = 1

# --- ნაბიჯი 1: VIN-ის სწრაფი სკანერი ---
if st.session_state.step == 1:
    st.title("📸 VIN Scanner")
    source = st.camera_input("დაასკანირეთ VIN გასაგრძელებლად")
    if source and st.button("გახსენი სამუშაო სივრცე ➡️"):
        # (აქ ჩაჯდება VIN-ის ამოცნობის ფუნქცია scan_text)
        st.session_state.vin = "5UXKR0C54E0H22781" # მაგალითისთვის
        st.session_state.step = 2
        st.rerun()

# --- ნაბიჯი 2: Split-Screen სამუშაო სივრცე ---
elif st.session_state.step == 2:
    # ეკრანის გაყოფა: 85% აუქციონი, 15% კონტროლი
    col_auction, col_tools = st.columns([8.5, 1.5])
    
    with col_auction:
        # აუქციონის გვერდი
        url = f"https://bidfax.info/index.php?do=search&subaction=search&story={st.session_state.vin}"
        st.components.v1.iframe(url, height=800, scrolling=True)

    with col_tools:
        st.markdown("### 🛠️ AI პანელი")
        st.write(f"VIN: `{st.session_state.vin}`")
        st.divider()
        
        # იმის გამო რომ ავტომატური სკრინშოტი დაბლოკილია, 
        # ვიყენებთ მობილურისთვის მოსახერხებელ ატვირთვას
        st.write("📸 **სკრინშოტის ატვირთვა:**")
        sc = st.file_uploader("Upload SC", label_visibility="collapsed", accept_multiple_files=True)
        
        if sc:
            st.success(f"მიღებულია {len(sc)} ფოტო")
            if st.button("🚀 ანალიზი"):
                st.session_state.screenshots = sc
                st.session_state.step = 3
                st.rerun()
        
        st.divider()
        if st.button("🔄 სხვა VIN"):
            st.session_state.step = 1
            st.rerun()

# --- ნაბიჯი 3: შედეგები ---
elif st.session_state.step == 3:
    st.subheader("📋 AI ანალიზის შედეგი")
    # აქ გამოჩნდება ანალიზი...
    if st.button("🔙 უკან სამუშაო სივრცეში"):
        st.session_state.step = 2
        st.rerun()
