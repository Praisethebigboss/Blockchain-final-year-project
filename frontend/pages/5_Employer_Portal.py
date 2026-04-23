import streamlit as st
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
from backend_client import BackendClient, BackendError
import apply_styles

st.set_page_config(page_title="Employer Portal", page_icon=":briefcase:")
apply_styles.apply_custom_styles()

if "employer_logged_in" not in st.session_state:
    st.session_state["employer_logged_in"] = False
if "employer_email" not in st.session_state:
    st.session_state["employer_email"] = None
if "employer_company" not in st.session_state:
    st.session_state["employer_company"] = None

auth.require_employer_auth()

st.title("Employer Portal")
st.markdown(f"**{st.session_state['employer_company']}**")

col_home, col_logout = st.columns([4, 1])
with col_home:
    st.page_link("main.py", label="Back to Home")
with col_logout:
    if st.button("Logout"):
        auth.employer_logout()
        st.rerun()

st.markdown("---")

default_backend = "http://127.0.0.1:8889"
default_frontend = "http://localhost:8501"
backend_url = st.sidebar.text_input("Backend URL", value=default_backend)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Logged in as:**")
st.sidebar.markdown(f"📧 {st.session_state['employer_email']}")
st.sidebar.markdown(f"🏢 {st.session_state['employer_company']}")
st.sidebar.markdown("---")
st.sidebar.markdown("**Requirements**")
st.sidebar.markdown("- Backend running on the URL above")
st.sidebar.markdown("- Hardhat node active on localhost:8545")

client = BackendClient(base_url=backend_url, frontend_url=default_frontend)

st.header("Verify a Transcript")

query_hash = st.query_params.get("verify", "")

hash_input = st.text_input(
    "Enter transcript hash",
    value=query_hash,
    placeholder="e.g. a1b2c3d4e5f6...",
    help="Enter the 64-character SHA-256 hash to verify",
)

if hash_input:
    if not re.compile(r"^[a-fA-F0-9]{64}$").match(hash_input):
        st.warning("Invalid hash format. Must be a 64-character hexadecimal string.")
    else:
        if st.button("Verify", type="primary") or query_hash:
            verification_ok = False
            exists = False
            transcript = None
            file_status = None
            
            with st.spinner("Verifying on blockchain..."):
                try:
                    result = client.verify_hash(hash_input)
                    exists = result.get("exists", False)
                    verification_ok = True
                except Exception as e:
                    st.error(f"Verification unavailable: {str(e)[:80]}")
                    st.info("Could not connect to backend. Please ensure backend is running.")

            if verification_ok:
                if exists:
                    st.success("**Verified!** This transcript exists on the blockchain.")

                    with st.spinner("Fetching details..."):
                        try:
                            transcript = client.get_transcript(hash_input)
                        except Exception:
                            pass
                    
                    if transcript:
                        st.markdown("---")
                        st.subheader("Transcript Details")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Issued by:**")
                            st.code(transcript["issuer"], language=None)
                        with col2:
                            st.markdown("**Issued at:**")
                            st.markdown(f"`{transcript['issued_at']}`")
                        st.markdown(f"**Document Hash:** `{transcript['document_hash']}`")

                    with st.spinner("Checking for original file..."):
                        try:
                            file_status = client.get_file_status(hash_input)
                            if file_status.get("stored"):
                                st.markdown("---")
                                st.subheader("Original File Available")
                                st.markdown(f"**Filename:** `{file_status['filename']}`")
                                st.markdown(f"**Size:** `{file_status['size'] / 1024:.1f} KB`")

                                try:
                                    download_data = client.download_file(hash_input)
                                    st.download_button(
                                        label="Download Original Transcript",
                                        data=download_data["data"],
                                        file_name=download_data["filename"],
                                        mime="application/octet-stream",
                                        use_container_width=True,
                                    )
                                except Exception:
                                    st.info("Download temporarily unavailable.")
                            else:
                                st.info("No original file stored. Only hash verification available.")
                        except Exception:
                            st.info("Original file not available.")

                    st.balloons()
                else:
                    st.error("**Not Found.** This transcript hash does not exist on the blockchain.")

st.markdown("---")
st.caption("Need help? Contact the issuing institution for verification.")
