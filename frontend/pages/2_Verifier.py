import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend_client import BackendClient, BackendError
from config import BACKEND_URL, FRONTEND_URL

HASH_PATTERN = np.compile(r"^[a-fA-F0-9]{64}$")

st.set_page_config(page_title="Verifier Portal", page_icon=":briefcase:")

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

client = BackendClient(base_url=BACKEND_URL, frontend_url=FRONTEND_URL)

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

import re
HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")

if hash_input:
    if not HASH_PATTERN.match(hash_input):
        st.warning("Invalid hash format. Must be a 64-character hexadecimal string.")
    else:
        if st.button("Verify", type="primary") or query_hash:
            with st.spinner("Verifying on blockchain..."):
                try:
                    result = client.verify_hash(hash_input)
                    if result.get("exists"):
                        st.success("**Verified!** This transcript exists on the blockchain.")
                        st.balloons()
                    else:
                        st.error("**Not Found.** This transcript hash does not exist on the blockchain.")
                except BackendError as e:
                    st.error(f"Verification failed: {e.message}")
