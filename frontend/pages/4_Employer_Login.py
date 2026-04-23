import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
import apply_styles

st.set_page_config(page_title="Employer Login", page_icon=":briefcase:")
apply_styles.apply_custom_styles()

if "employer_logged_in" not in st.session_state:
    st.session_state["employer_logged_in"] = False
if "employer_email" not in st.session_state:
    st.session_state["employer_email"] = None
if "employer_company" not in st.session_state:
    st.session_state["employer_company"] = None

if st.session_state.get("employer_logged_in"):
    st.switch_page("pages/5_Employer_Portal.py")

st.title("Employer Portal")
st.markdown("Verify academic transcripts from verified institutions.")

st.page_link("main.py", label="Back to Home")
st.markdown("---")

tab_login, tab_register = st.tabs(["Login", "Register"])

with tab_login:
    st.subheader("Login to Employer Portal")
    
    login_email = st.text_input("Email Address", placeholder="employer@company.com", key="employer_login_email")
    login_password = st.text_input("Password", type="password", key="employer_login_password")
    
    if st.button("Login", type="primary", use_container_width=True, key="employer_login_btn"):
        if not login_email or not login_password:
            st.warning("Please enter both email and password.")
        else:
            employer = auth.authenticate_employer(login_email, login_password)
            if employer:
                auth.employer_login(employer["email"], employer["company_name"])
                st.success(f"Welcome, {employer['company_name']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

with tab_register:
    st.subheader("Register as Employer")
    st.info("Anyone can register to verify academic transcripts.")
    
    reg_company = st.text_input("Company Name", placeholder="Acme Corporation", key="employer_reg_company")
    reg_email = st.text_input("Email Address", placeholder="employer@company.com", key="employer_reg_email")
    reg_password = st.text_input("Password", type="password", help="At least 6 characters", key="employer_reg_password")
    reg_confirm = st.text_input("Confirm Password", type="password", key="employer_reg_confirm")
    
    if st.button("Register", type="primary", use_container_width=True, key="employer_reg_btn"):
        if not reg_company or not reg_email or not reg_password or not reg_confirm:
            st.warning("Please fill in all fields.")
        elif reg_password != reg_confirm:
            st.error("Passwords do not match.")
        else:
            result = auth.register_employer(reg_email, reg_password, reg_company)
            if result["success"]:
                st.success("Registration successful! Please login.")
            else:
                st.error(result["message"])

st.markdown("---")
st.caption("Note: Employers can verify transcripts and download original documents.")
