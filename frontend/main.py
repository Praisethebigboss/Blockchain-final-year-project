import re
import tempfile
import streamlit as st
from backend_client import BackendClient, BackendError

HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")

st.set_page_config(page_title="Transcript Verification", page_icon=":scroll:")

st.title("Transcript Verification")
st.markdown("Issue and verify academic transcripts on the blockchain.")

backend_url = st.sidebar.text_input("Backend URL", value="http://127.0.0.1:8000")
st.sidebar.markdown("---")
st.sidebar.markdown("**Requirements**")
st.sidebar.markdown("- Backend running on the URL above")
st.sidebar.markdown("- Hardhat node active on localhost:8545")

client = BackendClient(base_url=backend_url)

tab_issue, tab_verify = st.tabs(["Issue Transcript", "Verify Transcript"])

with tab_issue:
    st.header("Issue a Transcript")

    uploaded_file = st.file_uploader(
        "Upload transcript file",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Supported: PDF, PNG, JPG",
    )

    if uploaded_file is not None:
        with st.spinner("Generating hash..."):
            try:
                file_bytes = uploaded_file.getvalue()
                result = client.upload_file_bytes(file_bytes, uploaded_file.name)
                file_hash = result["hash"]

                st.success("File hashed successfully")
                st.code(file_hash, language=None)

                if st.button("Store on Blockchain", type="primary"):
                    with st.spinner("Storing on blockchain..."):
                        try:
                            store_result = client.store_hash(file_hash)
                            st.success("Stored on blockchain!")
                            st.markdown(f"**Transaction Hash:** `{store_result['tx']}`")
                        except BackendError as e:
                            st.error(f"Failed to store: {e.message}")
            except BackendError as e:
                st.error(f"Failed to hash file: {e.message}")

with tab_verify:
    st.header("Verify a Transcript")

    hash_input = st.text_input(
        "Enter transcript hash",
        placeholder="e.g. a1b2c3d4e5f6...",
        help="Enter the 64-character SHA-256 hash to verify",
    )

    if hash_input:
        if not HASH_PATTERN.match(hash_input):
            st.warning("Invalid hash format. Must be a 64-character hexadecimal string.")
        else:
            if st.button("Verify", type="primary"):
                with st.spinner("Verifying on blockchain..."):
                    try:
                        result = client.verify_hash(hash_input)
                        if result.get("exists"):
                            st.success("**Verified!** This transcript exists on the blockchain.")
                        else:
                            st.error("**Not Found.** This transcript hash does not exist on the blockchain.")
                    except BackendError as e:
                        st.error(f"Verification failed: {e.message}")
