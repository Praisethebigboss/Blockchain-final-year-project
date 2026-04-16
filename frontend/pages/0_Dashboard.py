import streamlit as st
import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
from backend_client import BackendClient, BackendError
import apply_styles

st.set_page_config(page_title="Dashboard — Issuer Portal", page_icon=":chart:")
apply_styles.apply_custom_styles()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "institution" not in st.session_state:
    st.session_state["institution"] = None

if not st.session_state.get("logged_in"):
    st.warning("Please log in to access the dashboard.")
    st.page_link("pages/Login.py", label="Go to Login")
    st.stop()

st.title(f"Issuer Dashboard — {st.session_state['institution']}")

col_home, col_issuer, col_logout = st.columns([1, 1, 1])
with col_home:
    st.page_link("main.py", label="Home")
with col_issuer:
    st.page_link("pages/1_Issuer.py", label="Issue Transcript")
with col_logout:
    if st.button("Logout"):
        auth.logout()
        st.rerun()

st.markdown("---")

client = BackendClient()

PAGE_SIZE = 10

if "transcript_page" not in st.session_state:
    st.session_state["transcript_page"] = 0

search_query = st.text_input(
    "Search Transcripts",
    placeholder="Enter hash to search...",
    help="Enter a partial or full transcript hash to search",
)

offset = st.session_state["transcript_page"] * PAGE_SIZE

try:
    result = client.list_transcripts(offset=offset, limit=PAGE_SIZE)
    total = result.get("total", 0)
    transcripts = result.get("transcripts", [])
    
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE if total > 0 else 0
    
    st.subheader(f"Issued Transcripts ({total:,})")
    
    if search_query:
        search_query = search_query.lower()
        transcripts = [
            t for t in transcripts 
            if search_query in t.get("hash", "").lower() or 
               search_query in t.get("issuer", "").lower()
        ]
        st.info(f"Showing {len(transcripts)} results for '{search_query}'")
    
    if not transcripts:
        st.info("No transcripts issued yet.")
    else:
        for t in transcripts:
            with st.container():
                col_hash, col_issuer, col_date, col_action = st.columns([3, 2, 2, 1])
                with col_hash:
                    st.code(t.get("hash", "")[:20] + "...", language=None)
                with col_issuer:
                    st.caption(f"Issuer: {t.get('issuer', '')[:10]}...")
                with col_date:
                    ts = t.get("timestamp", 0)
                    if ts:
                        date = datetime.datetime.fromtimestamp(ts)
                        st.caption(date.strftime("%Y-%m-%d %H:%M"))
                    else:
                        st.caption("N/A")
                with col_action:
                    hash_value = t.get("hash", "")
                    verify_url = f"../3_Student.py?verify={hash_value}"
                    st.page_link(verify_url, label="View")
                st.divider()
        
        if not search_query and total_pages > 1:
            st.markdown("---")
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            
            with col_prev:
                if st.session_state["transcript_page"] > 0:
                    if st.button("← Previous", key="prev_page"):
                        st.session_state["transcript_page"] -= 1
                        st.rerun()
            
            with col_info:
                st.caption(f"Page {st.session_state['transcript_page'] + 1} of {total_pages}")
            
            with col_next:
                if st.session_state["transcript_page"] < total_pages - 1:
                    if st.button("Next →", key="next_page"):
                        st.session_state["transcript_page"] += 1
                        st.rerun()

except BackendError as e:
    st.error(f"Failed to load transcripts: {e.message}")
    st.info("Make sure the backend is running and the blockchain is accessible.")
except Exception as e:
    st.error(f"An error occurred: {e}")