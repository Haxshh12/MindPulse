import streamlit as st
import pandas as pd
import os
from utils.admin_utils import load_users, save_users, load_user_inputs, save_user_inputs, load_psychologists, save_psychologists

def admin_dashboard():
    st.title("🔧 Admin Dashboard")

    # Load all dataframes
    users_df = load_users()
    user_inputs_df = load_user_inputs()
    psych_df = load_psychologists()

    st.subheader("Registered Users")
    st.dataframe(users_df)

    st.subheader("User Mental Health Data")
    st.dataframe(user_inputs_df)

    st.markdown("---")
    st.write("### Edit User Mental Health Data")
    st.write("To edit, download the CSV below, modify offline, then upload the updated file.")

    csv_user_data = user_inputs_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download User Mental Health Data CSV", csv_user_data, "user_inputs.csv", "text/csv")

    uploaded_user_file = st.file_uploader("Upload Updated User Mental Health Data CSV", type=["csv"])
    if uploaded_user_file is not None:
        try:
            new_user_df = pd.read_csv(uploaded_user_file)
            save_user_inputs(new_user_df)
            st.success("✅ User Mental Health Data updated successfully!")
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")

    st.markdown("---")
    st.write("### Edit Psychologists & Counsellors")
    st.dataframe(psych_df)

    csv_psych = psych_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Psychologists Data CSV", csv_psych, "psychologists.csv", "text/csv")

    uploaded_psych_file = st.file_uploader("Upload Updated Psychologists Data CSV", type=["csv"])
    if uploaded_psych_file is not None:
        try:
            new_psych_df = pd.read_csv(uploaded_psych_file)
            save_psychologists(new_psych_df)
            st.success("✅ Psychologists data updated successfully!")
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
