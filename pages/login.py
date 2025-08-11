import streamlit as st
from utils.auth import register_user, authenticate_user

def login_page():
    st.title("🧠 MindPulse - Login / Register")

    # Choose between login and register
    option = st.radio("Choose an option", ["Login", "Register"], horizontal=True)

    if option == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            result = authenticate_user(email, password)
            if result:
                role, name = result
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.name = name
                st.session_state.email = email
                st.success(f"Welcome {name}!")
            else:
                st.error("Invalid credentials!")

    elif option == "Register":
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])

        if st.button("Register"):
            success, msg = register_user(email, password, name, role)
            if success:
                st.success(msg)
            else:
                st.error(msg)
