import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend_client import BackendClient, BackendError
from config import BACKEND_URL, FRONTEND_URL

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

client = BackendClient(base_url=BACKEND_URL, frontend_url=FRONTEND_URL)

query_hash = st.query_params.get("verify", "")

if not query_hash:
    st.header("No Verification Link Provided")
    st.info(
        "To verify your transcript, please open the verification link "
        "provided by your institution. The link should look like:\n\n"
        "`http://localhost:8501/Student/?verify=<hash>`"
    )
    st.stop()

import re
HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")

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
            st.markdown(f"**Hash:** `{query_hash}`")
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
