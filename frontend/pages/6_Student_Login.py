import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
import apply_styles

st.set_page_config(page_title="Student Login", page_icon=":student:")
apply_styles.apply_custom_styles()

if "student_logged_in" not in st.session_state:
    st.session_state["student_logged_in"] = False
if "student_email" not in st.session_state:
    st.session_state["student_email"] = None
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None
if "student_name" not in st.session_state:
    st.session_state["student_name"] = None

if st.session_state.get("student_logged_in"):
    st.switch_page("pages/7_Student_Dashboard.py")

st.title("Student Portal")
st.markdown("Access your academic transcripts.")

st.page_link("main.py", label="Back to Home")
st.markdown("---")

tab_login, tab_register = st.tabs(["Login", "Register"])

with tab_login:
    st.subheader("Login to Your Account")
    
    login_email = st.text_input("Email Address", placeholder="student@school.edu", key="student_login_email")
    login_password = st.text_input("Password", type="password", key="student_login_password")
    
    if st.button("Login", type="primary", use_container_width=True, key="student_login_btn"):
        if not login_email or not login_password:
            st.warning("Please enter both email and password.")
        else:
            student = auth.authenticate_student(login_email, login_password)
            if student:
                auth.student_login(
                    student["email"],
                    student.get("student_id", ""),
                    student.get("full_name", "")
                )
                st.success(f"Welcome, {student.get('full_name') or student['email']}!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
    
    st.markdown("---")
    st.info("Don't have an account? Register below.")

with tab_register:
    st.subheader("Register as Student")
    st.info("Enter your school email to access your transcripts.")
    
    reg_email = st.text_input("Email Address", placeholder="student@school.edu", key="student_reg_email")
    reg_student_id = st.text_input("Student ID (Optional)", placeholder="e.g., 2021001234", key="student_reg_id")
    reg_name = st.text_input("Full Name (Optional)", placeholder="John Doe", key="student_reg_name")
    reg_password = st.text_input("Password", type="password", help="At least 4 characters", key="student_reg_password")
    reg_confirm = st.text_input("Confirm Password", type="password", key="student_reg_confirm")
    
    if st.button("Register", type="primary", use_container_width=True, key="student_reg_btn"):
        if not reg_email or not reg_password or not reg_confirm:
            st.warning("Please fill in required fields.")
        elif reg_password != reg_confirm:
            st.error("Passwords do not match.")
        else:
            result = auth.register_student(reg_email, reg_password, reg_student_id, reg_name)
            if result["success"]:
                st.success("Registration successful! Please login.")
            else:
                st.error(result["message"])

st.markdown("---")
st.caption("Note: Your transcripts will be available after your institution issues them to your email.")