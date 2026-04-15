import streamlit as st
from pathlib import Path

def apply_custom_styles():
    css_path = Path(__file__).parent / "custom_style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)