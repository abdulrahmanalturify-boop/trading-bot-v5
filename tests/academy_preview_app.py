"""Isolated academy harness for Streamlit AppTest; never calls live market feeds."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import streamlit as st
st.set_page_config(layout='wide',page_title='Academy test')
st.session_state.setdefault('lang','en')
st.sidebar.selectbox('Language / اللغة',['en','ar'],key='lang')
import theme as T
import p_academy
st.markdown(T.CSS+(T.RTL_CSS if st.session_state.lang=='ar' else ''),unsafe_allow_html=True)
p_academy.page_academy()
