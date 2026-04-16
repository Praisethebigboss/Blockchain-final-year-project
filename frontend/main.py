import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import auth

st.set_page_config(page_title="Transcript Verification", page_icon=":scroll:", layout="wide")

import apply_styles
apply_styles.apply_custom_styles()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

st.title("Transcript Verification")
st.markdown("A blockchain-based system for issuing and verifying academic transcripts.")

st.markdown("---")
st.subheader("Select Your Role")

col_issuer, col_verifier, col_student = st.columns(3)

with col_issuer:
    st.markdown("### 🏛️ Issuer")
    st.markdown("**University / Institution**")
    st.markdown("Issue transcripts and generate shareable verification links.")
    if st.button("Open Issuer Portal", key="issuer_btn"):
        if st.session_state.get("logged_in"):
            st.switch_page("pages/1_Issuer.py")
        else:
            st.switch_page("pages/Login.py")

with col_verifier:
    st.markdown("### 💼 Verifier")
    st.markdown("**Employer / Institution**")
    st.markdown("Verify transcript hashes against the blockchain.")
    if st.button("Open Verifier Portal", key="verifier_btn"):
        st.switch_page("pages/2_Verifier.py")

with col_student:
    st.markdown("### 🎓 Student")
    st.markdown("**Verify Your Transcript**")
    st.markdown("Check if your transcript has been issued on the blockchain.")
    if st.button("Open Student Portal", key="student_btn"):
        st.switch_page("pages/3_Student.py")

st.markdown("---")

if st.session_state.get("logged_in"):
    st.success(f"Logged in as: **{st.session_state['institution']}**")

st.markdown("### How It Works")
st.markdown("""
1. The **Issuer** uploads a transcript file and stores its SHA-256 hash on the blockchain.
2. A **shareable verification link** is generated for the student.
3. The **Verifier** (employer/institution) opens the link or enters the hash to confirm authenticity.
4. The blockchain ensures the transcript has not been tampered with or forged.
""")
