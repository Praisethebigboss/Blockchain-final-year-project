import streamlit as st
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
from backend_client import BackendClient, BackendError
import apply_styles

st.set_page_config(page_title="Student Dashboard", page_icon=":student:")
apply_styles.apply_custom_styles()

if "student_logged_in" not in st.session_state:
    st.session_state["student_logged_in"] = False
if "student_email" not in st.session_state:
    st.session_state["student_email"] = None
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None
if "student_name" not in st.session_state:
    st.session_state["student_name"] = None

auth.require_student_auth()

st.title(f"Student Dashboard")
st.markdown(f"**Welcome, {st.session_state['student_name'] or st.session_state['student_email']}**")

col_home, col_logout = st.columns([4, 1])
with col_home:
    st.page_link("main.py", label="Back to Home")
with col_logout:
    if st.button("Logout"):
        auth.student_logout()
        st.rerun()

st.markdown("---")

default_backend = "http://127.0.0.1:8889"
default_frontend = "http://localhost:8501"
backend_url = st.sidebar.text_input("Backend URL", value=default_backend)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Logged in as:**")
st.sidebar.markdown(f"📧 {st.session_state['student_email']}")
if st.session_state.get("student_id"):
    st.sidebar.markdown(f"🎓 ID: {st.session_state['student_id']}")
st.sidebar.markdown("---")
st.sidebar.markdown("Your transcripts will appear below after your institution issues them.")

client = BackendClient(base_url=backend_url, frontend_url=default_frontend)

st.header("My Transcripts")

try:
    result = client.get_student_transcripts(st.session_state["student_email"])
    transcripts = result.get("transcripts", [])
    
    if not transcripts:
        st.info("No transcripts found. Your institution has not yet issued any transcripts to your email.")
    else:
        st.success(f"Found {len(transcripts)} transcript(s)")
        
        for t in transcripts:
            hash_val = t.get("hash", "")
            used = t.get("used", False)
            transcript_info = t.get("transcript", {})
            
            with st.expander(f"📄 Transcript - {hash_val[:20]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Hash:**")
                    st.code(hash_val, language=None)
                with col2:
                    status = "✅ Available" if not used else "❌ Already Downloaded"
                    st.markdown(f"**Status:** {status}")
                
                if transcript_info:
                    st.markdown("---")
                    st.markdown(f"**Issued by:** `{transcript_info.get('issuer', 'N/A')}`")
                    st.markdown(f"**Issued at:** `{transcript_info.get('issued_at', 'N/A')}`")
                
                created = t.get("created_at", 0)
                if created:
                    date = datetime.datetime.fromtimestamp(created)
                    st.markdown(f"**Issue Date:** {date.strftime('%Y-%m-%d %H:%M')}")
                
                expires = t.get("expires_at", 0)
                if expires:
                    exp_date = datetime.datetime.fromtimestamp(expires)
                    st.markdown(f"**Expires:** {exp_date.strftime('%Y-%m-%d %H:%M')}")
                
                st.markdown("---")
                
                if not used:
                    try:
                        file_status = client.get_file_status(hash_val)
                        if file_status.get("stored"):
                            st.success("📥 Original file available for download")
                            
                            download_data = client.download_file(hash_val)
                            st.download_button(
                                label="Download Transcript",
                                data=download_data["data"],
                                file_name=download_data["filename"],
                                mime="application/octet-stream",
                                use_container_width=True,
                            )
                            
                            if st.button("Mark as Downloaded", key=f"download_{hash_val[:10]}", type="primary"):
                                try:
                                    client.use_student_token(hash_val)
                                    st.success("Download recorded!")
                                    st.rerun()
                                except Exception as e:
                                    st.warning(f"Note: {e}")
                        else:
                            st.info("Original file not stored by institution.")
                    except Exception as e:
                        st.info(f"File not available: {e}")
                else:
                    st.warning("This transcript has already been downloaded.")

except BackendError as e:
    st.error(f"Failed to load transcripts: {e.message}")
    st.info("Make sure the backend and blockchain are running.")
except Exception as e:
    st.error(f"An error occurred: {e}")

st.markdown("---")
st.caption("Need help? Contact your institution for assistance.")