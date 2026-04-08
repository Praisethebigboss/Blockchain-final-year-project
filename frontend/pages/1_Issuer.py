import streamlit as st
import datetime
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
from backend_client import BackendClient, BackendError, DuplicateError

HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")

st.set_page_config(page_title="Issuer Portal", page_icon=":university:")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

auth.require_auth()

st.title("Issuer Portal")
st.markdown(f"**{st.session_state['institution']}**")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Logout"):
        auth.logout()
        st.rerun()
with col2:
    st.page_link("main.py", label="Back to Home")

st.markdown("---")

default_backend = "http://127.0.0.1:8000"
default_frontend = "http://localhost:8501"
backend_url = st.sidebar.text_input("Backend URL", value=default_backend)
st.sidebar.markdown("---")
st.sidebar.markdown("**Requirements**")
st.sidebar.markdown("- Backend running on the URL above")
st.sidebar.markdown("- Hardhat node active on localhost:8545")
st.sidebar.markdown("- IPFS daemon running on port 5001")

client = BackendClient(base_url=backend_url, frontend_url=default_frontend)

if "issue_history" not in st.session_state:
    st.session_state["issue_history"] = []
if "last_issued" not in st.session_state:
    st.session_state["last_issued"] = None

st.header("Issue a Transcript")

uploaded_file = st.file_uploader(
    "Upload Transcript File",
    type=["pdf", "png", "jpg", "jpeg"],
    help="Supported: PDF, PNG, JPG (max 10MB)",
)

if uploaded_file is not None:
    with st.spinner("Generating hash..."):
        try:
            file_bytes = uploaded_file.getvalue()
            result = client.upload_file_bytes(file_bytes, uploaded_file.name)
            file_hash = result["hash"]
            st.session_state["last_issued"] = {
                "filename": uploaded_file.name,
                "hash": file_hash,
                "file_bytes": file_bytes,
                "size": len(file_bytes),
            }
            st.success("File hashed successfully!")
            st.code(file_hash, language=None)
            st.info(f"File size: {len(file_bytes) / 1024:.1f} KB")
        except BackendError as e:
            st.error(f"Failed to hash file: {e.message}")
            st.session_state["last_issued"] = None

if st.session_state.get("last_issued") is not None:
    issue_data = st.session_state["last_issued"]
    st.markdown("---")
    st.subheader("Store on Blockchain")

    col_hash, col_btn = st.columns([3, 1])
    with col_hash:
        st.code(issue_data["hash"], language=None)
    with col_btn:
        store_clicked = st.button("Store on Blockchain", type="primary", use_container_width=True)

    if store_clicked:
        with st.spinner("Storing on blockchain..."):
            try:
                store_result = client.store_hash(issue_data["hash"])
                st.success("Stored on blockchain!")
                st.markdown(f"**Transaction Hash:** `{store_result['tx']}`")
            except DuplicateError as e:
                st.warning(f"⚠️ {e.message}")
                st.session_state["last_issued"] = None
                st.rerun()
            except BackendError as e:
                st.error(f"Failed to store: {e.message}")
                st.rerun()

        with st.spinner("Uploading to IPFS..."):
            try:
                file_result = client.store_file(issue_data["file_bytes"], issue_data["filename"])
                st.success("File uploaded to IPFS!")
                st.markdown(f"**IPFS CID:** `{file_result['cid']}`")
                ipfs_stored = True
            except BackendError as e:
                st.warning(f"⚠️ IPFS upload failed: {e.message}. File not stored.")
                ipfs_stored = False
            except Exception as e:
                st.warning(f"⚠️ IPFS upload failed: {str(e)}. File not stored.")
                ipfs_stored = False

        verify_url = client.get_verification_url(issue_data["hash"])
        st.markdown("---")
        st.subheader("Shareable Verification Link")
        st.code(verify_url, language=None)

        download_url = client.get_download_url(issue_data["hash"])

        col_verify, col_download = st.columns(2)
        with col_verify:
            st.markdown(
                f'<a href="{verify_url}" target="_blank">'
                f'<button style="background-color:#FF4B4B;color:white;padding:10px 20px;'
                f'border:none;border-radius:6px;cursor:pointer;width:100%;font-size:14px;">'
                f"Open Verification Page</button>"
                f"</a>",
                unsafe_allow_html=True,
            )
        with col_download:
            st.markdown(
                f'<a href="{download_url}" download="{issue_data['filename']}">'
                f'<button style="background-color:#4CAF50;color:white;padding:10px 20px;'
                f'border:none;border-radius:6px;cursor:pointer;width:100%;font-size:14px;">'
                f"Download Original</button>"
                f"</a>",
                unsafe_allow_html=True,
            )

        st.session_state["issue_history"].insert(0, {
            "filename": issue_data["filename"],
            "hash": issue_data["hash"],
            "tx": store_result.get("tx", "N/A"),
            "ipfs": "Yes" if ipfs_stored else "No",
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        st.session_state["last_issued"] = None
        st.rerun()

if st.session_state["issue_history"]:
    st.markdown("---")
    st.header("Issue History")

    for item in st.session_state["issue_history"]:
        with st.expander(f"📄 {item['filename']} — {item['time']}"):
            st.markdown(f"**Hash:** `{item['hash']}`")
            st.markdown(f"**Transaction:** `{item['tx']}`")
            st.markdown(f"**IPFS Stored:** {item['ipfs']}")
            col_down, col_link = st.columns(2)
            with col_down:
                st.markdown(
                    f'<a href="{client.get_download_url(item['hash'])}" download="{item['filename']}">'
                    f'<button style="background-color:#4CAF50;color:white;padding:8px 16px;'
                    f'border:none;border-radius:6px;cursor:pointer;width:100%;">'
                    f"Download Original</button>"
                    f"</a>",
                    unsafe_allow_html=True,
                )
            with col_link:
                st.markdown(
                    f'<a href="{client.get_verification_url(item['hash'])}" target="_blank">'
                    f'<button style="background-color:#FF4B4B;color:white;padding:8px 16px;'
                    f'border:none;border-radius:6px;cursor:pointer;width:100%;">'
                    f"Verification Link</button>"
                    f"</a>",
                    unsafe_allow_html=True,
                )
