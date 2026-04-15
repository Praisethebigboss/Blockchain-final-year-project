import streamlit as st
import auth
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import apply_styles

st.set_page_config(page_title="Login — Issuer Portal", page_icon=":lock:")
apply_styles.apply_custom_styles()

st.title("Issuer Login")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

if st.session_state.get("logged_in"):
    st.success(f"Already logged in as **{st.session_state['institution']}**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/0_Dashboard.py", label="Dashboard")
    with col2:
        st.page_link("pages/1_Issuer.py", label="Go to Issuer Portal")
    with col3:
        if st.button("Logout"):
            auth.logout()
            st.rerun()
    st.stop()

tab_login, tab_register = st.tabs(["Login", "Create Account"])

with tab_login:
    st.header("Sign In")
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = auth.authenticate(username, password)
                if user:
                    auth.login(user["username"], user["institution"])
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

with tab_register:
    st.header("Create Account")
    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Choose a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        institution = st.text_input("Institution Name", placeholder="e.g. University of Lagos")
        submitted = st.form_submit_button("Create Account")
        if submitted:
            if not username or not password or not institution:
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                if auth.create_user(username, password, institution):
                    st.success("Account created! Please log in.")
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose a different one.")

st.markdown("---")
st.caption("Default admin credentials: **admin / admin123**")
