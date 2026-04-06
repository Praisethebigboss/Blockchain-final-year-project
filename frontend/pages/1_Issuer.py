import streamlit as st
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
from backend_client import BackendClient, BackendError, DuplicateError
from config import BACKEND_URL, FRONTEND_URL

st.set_page_config(page_title="Issuer Portal", page_icon=":university:")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

auth.require_auth()

st.title(f"Issuer Portal")
st.markdown(f"**{st.session_state['institution']}**")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Logout"):
        auth.logout()
        st.rerun()
with col2:
    st.page_link("main.py", label="Back to Home")

st.markdown("---")

client = BackendClient(base_url=BACKEND_URL, frontend_url=FRONTEND_URL)

if "issue_history" not in st.session_state:
    st.session_state["issue_history"] = []

st.header("Issue a Transcript")

with st.form("issue_form", clear_on_submit=True):
    institution_name = st.text_input(
        "Institution Name",
        value=st.session_state["institution"],
        disabled=True,
        help="Your institution name from your account"
    )
    uploaded_file = st.file_uploader(
        "Upload Transcript File",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Supported: PDF, PNG, JPG"
    )
    submitted = st.form_submit_button("Issue Transcript")
    if submitted and uploaded_file:
        with st.spinner("Generating hash..."):
            try:
                file_bytes = uploaded_file.getvalue()
                result = client.upload_file_bytes(file_bytes, uploaded_file.name)
                file_hash = result["hash"]
                st.success("File hashed successfully!")
                st.code(file_hash, language=None)
            except BackendError as e:
                st.error(f"Failed to hash file: {e.message}")
                st.stop()

        with st.spinner("Storing on blockchain..."):
            try:
                store_result = client.store_hash(file_hash)
                st.success("Stored on blockchain!")
                st.markdown(f"**Transaction Hash:** `{store_result['tx']}`")

                verify_url = client.get_verification_url(file_hash)
                st.markdown("### Shareable Verification Link")
                st.code(verify_url, language=None)

                st.session_state["issue_history"].insert(0, {
                    "filename": uploaded_file.name,
                    "hash": file_hash,
                    "tx": store_result["tx"],
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                col1, col2 = st.columns(2)
                with col1:
                    st.code(verify_url, language=None)
                with col2:
                    st.markdown(
                        f'<a href="{verify_url}" target="_blank">'
                        f'<button style="background-color:#FF4B4B;color:white;padding:8px 16px;border:none;border-radius:6px;cursor:pointer;width:100%;">Open Verification Page</button>'
                        f"</a>",
                        unsafe_allow_html=True,
                    )
            except DuplicateError as e:
                st.warning(f"⚠️ {e.message}")
            except BackendError as e:
                st.error(f"Failed to store: {e.message}")

if st.session_state["issue_history"]:
    st.markdown("---")
    st.header("Issue History")
    st.data_editor(
        st.session_state["issue_history"],
        column_config={
            "filename": st.column_config.TextColumn("Filename"),
            "hash": st.column_config.TextColumn("Hash (truncated)", width="medium"),
            "tx": st.column_config.TextColumn("Transaction Hash", width="medium"),
            "time": st.column_config.TextColumn("Issued At"),
        },
        hide_index=True,
        use_container_width=True,
    )
