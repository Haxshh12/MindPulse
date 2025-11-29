import streamlit as st
from pages.login import login_page
from pages.user_dashboard_2 import user_dashboard
from pages.admin_dashboard_2 import admin_dashboard

# Initialize session vars if not set
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.name = None
    st.session_state.email = None

# Navigation
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "admin":
        admin_dashboard()
    else:
        user_dashboard()
