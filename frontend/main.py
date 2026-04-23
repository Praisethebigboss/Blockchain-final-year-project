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
if "employer_logged_in" not in st.session_state:
    st.session_state["employer_logged_in"] = False
if "employer_email" not in st.session_state:
    st.session_state["employer_email"] = None
if "employer_company" not in st.session_state:
    st.session_state["employer_company"] = None
if "student_logged_in" not in st.session_state:
    st.session_state["student_logged_in"] = False
if "student_email" not in st.session_state:
    st.session_state["student_email"] = None
if "student_name" not in st.session_state:
    st.session_state["student_name"] = None

st.title("Transcript Verification")
st.markdown("A blockchain-based system for issuing and verifying academic transcripts.")

st.markdown("---")
st.subheader("Select Your Role")

col_issuer, col_student, col_employer = st.columns(3)

with col_issuer:
    st.markdown("### 🏛️ Issuer")
    st.markdown("**University / Institution**")
    st.markdown("Issue transcripts and generate shareable verification links.")
    if st.button("Open Issuer Portal", key="issuer_btn"):
        if st.session_state.get("logged_in"):
            st.switch_page("pages/1_Issuer.py")
        else:
            st.switch_page("pages/Login.py")

with col_student:
    st.markdown("### 🎓 Student")
    st.markdown("**View Your Transcripts**")
    st.markdown("Login to see and download your issued transcripts.")
    if st.button("Student Dashboard", key="student_btn"):
        st.switch_page("pages/7_Student_Dashboard.py")

with col_employer:
    st.markdown("### 💼 Employer")
    st.markdown("**Verify Transcripts**")
    st.markdown("Login to verify and download transcript documents.")
    if st.button("Open Employer Portal", key="employer_btn"):
        st.switch_page("pages/4_Employer_Login.py")

st.markdown("---")

if st.session_state.get("logged_in"):
    st.success(f"Issuer logged in as: **{st.session_state['institution']}**")
elif st.session_state.get("employer_logged_in"):
    st.success(f"Employer logged in as: **{st.session_state['employer_company']}**")
elif st.session_state.get("student_logged_in"):
    st.success(f"Student logged in as: **{st.session_state['student_name'] or st.session_state['student_email']}**")

st.markdown("### How It Works")
st.markdown("""
1. The **Issuer** (university) uploads a transcript and stores its hash on the blockchain.
2. The **Student** logs in to view and download their issued transcripts.
3. The **Employer** logs in to verify transcripts and download original documents.
4. The blockchain ensures transcripts cannot be tampered with or forged.
""")
