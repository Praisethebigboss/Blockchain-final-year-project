import streamlit as st
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend_client import BackendClient, BackendError
import apply_styles

HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")

st.set_page_config(page_title="Verifier Portal", page_icon=":briefcase:")
apply_styles.apply_custom_styles()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

st.title("Verifier Portal")
st.markdown("Verify academic transcript hashes against the blockchain.")

st.page_link("main.py", label="Back to Home")
st.markdown("---")

default_backend = "http://127.0.0.1:8888"
default_frontend = "http://localhost:8501"
backend_url = st.sidebar.text_input("Backend URL", value=default_backend)
st.sidebar.markdown("---")
st.sidebar.markdown("**Requirements**")
st.sidebar.markdown("- Backend running on the URL above")
st.sidebar.markdown("- Hardhat node active on localhost:8545")
st.sidebar.markdown("- IPFS daemon running on port 5001")

client = BackendClient(base_url=backend_url, frontend_url=default_frontend)

query_hash = st.query_params.get("verify", "")

st.header("Verify a Transcript")

if query_hash:
    st.info(f"Verification link received for hash: `{query_hash}`")

hash_input = st.text_input(
    "Enter transcript hash",
    value=query_hash,
    placeholder="e.g. a1b2c3d4e5f6...",
    help="Enter the 64-character SHA-256 hash to verify",
)

if hash_input:
    if not HASH_PATTERN.match(hash_input):
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

                                download_url = client.get_download_url(hash_input)
                                st.markdown(
                                    f'<a href="{download_url}" download="{file_status["filename"]}">'
                                    f'<button style="background-color:#4CAF50;color:white;padding:12px 24px;'
                                    f'border:none;border-radius:6px;cursor:pointer;width:100%;font-size:16px;">'
                                    f"Download Original Transcript</button>"
                                    f"</a>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.info("No original file stored. Only hash verification available.")
                        except Exception:
                            st.info("Original file not available.")

                    st.balloons()
                else:
                    st.error("**Not Found.** This transcript hash does not exist on the blockchain.")
