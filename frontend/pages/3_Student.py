import streamlit as st
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend_client import BackendClient, BackendError

HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")

st.set_page_config(page_title="Student — Verify Transcript", page_icon=":student:")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

st.title("Student Portal")
st.markdown("Check the verification status of your transcript.")

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

query_hash = st.query_params.get("verify", "")

if not query_hash:
    st.header("No Verification Link Provided")
    st.info(
        "To verify your transcript, please open the verification link "
        "provided by your institution. The link should look like:\n\n"
        "`http://localhost:8501/pages/3_Student.py?verify=<hash>`"
    )
    st.stop()

if not HASH_PATTERN.match(query_hash):
    st.error("Invalid hash format in verification link.")
    st.stop()

st.header("Verifying Your Transcript...")
with st.spinner("Checking blockchain..."):
    try:
        result = client.verify_hash(query_hash)
        if result.get("exists"):
            st.markdown("## ✅ Your Transcript is Verified")
            st.success(
                "This transcript hash exists on the blockchain and has been "
                "issued by an authorized institution."
            )

            with st.spinner("Fetching details..."):
                transcript = client.get_transcript(query_hash)
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
                    file_status = client.get_file_status(query_hash)
                    if file_status.get("stored"):
                        st.markdown("---")
                        st.subheader("Original Transcript Available")
                        st.markdown(f"**Filename:** `{file_status['filename']}`")
                        st.markdown(f"**Size:** `{file_status['size'] / 1024:.1f} KB`")

                        download_url = client.get_download_url(query_hash)
                        st.markdown(
                            f'<a href="{download_url}" download="{file_status["filename"]}">'
                            f'<button style="background-color:#4CAF50;color:white;padding:14px 28px;'
                            f'border:none;border-radius:6px;cursor:pointer;width:100%;font-size:18px;">'
                            f"Download My Transcript</button>"
                            f"</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("Original file not stored. Contact your institution for the document.")
                except BackendError:
                    st.info("Original file not available for download.")

            st.balloons()
        else:
            st.markdown("## ❌ Transcript Not Found")
            st.error(
                "This transcript hash was not found on the blockchain. "
                "Please contact your institution."
            )
            st.markdown(f"**Hash:** `{query_hash}`")
    except BackendError as e:
        st.error(f"Verification failed: {e.message}")

st.markdown("---")
st.caption("Having trouble? Contact your institution for assistance.")
